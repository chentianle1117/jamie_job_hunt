#!/usr/bin/env python3
"""Extract tailored resume HTML files into JSON format."""

import json
import re
import os
import sys
import html as html_mod


def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def convert_kw_spans(text):
    """Convert <span class="kw" data-kwg="X">text</span> and
       <span class="jd-kw" data-kwg="X">text</span> to {X|text}."""
    # class then data-kwg
    text = re.sub(
        r'<span\s+class="(?:jd-)?kw"\s+data-kwg="([^"]+)">(.*?)</span>',
        r'{\1|\2}', text)
    # data-kwg then class
    text = re.sub(
        r'<span\s+data-kwg="([^"]+)"\s+class="(?:jd-)?kw">(.*?)</span>',
        r'{\1|\2}', text)
    return text


def strip_tags(text):
    """Remove all HTML tags."""
    return re.sub(r'<[^>]+>', '', text)


def decode_entities(text):
    """Decode common HTML entities."""
    text = text.replace('&amp;', '&')
    text = text.replace('&ndash;', '\u2013')
    text = text.replace('&mdash;', '\u2014')
    text = text.replace('&rsquo;', '\u2019')
    text = text.replace('&lsquo;', '\u2018')
    text = text.replace('&bull;', '\u2022')
    text = text.replace('&middot;', '\u00b7')
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&#39;', "'")
    return text


def clean_bullet_text(text):
    """Convert kw spans, strip tags, remove bullet prefix, decode entities."""
    text = convert_kw_spans(text)
    text = strip_tags(text)
    text = decode_entities(text)
    text = re.sub(r'^[\u2022\u00b7]\s*', '', text.strip())
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_page_margins(html):
    m = re.search(r'@page\s*\{[^}]*margin:\s*([^;]+);', html)
    if m:
        parts = m.group(1).strip().split()
        if len(parts) == 4:
            return {"top": parts[0], "right": parts[1], "bottom": parts[2], "left": parts[3]}
    return {"top": "0.45in", "right": "0.45in", "bottom": "0.35in", "left": "0.45in"}


def parse_filename_meta(filename):
    """Parse company, role, date from filename pattern:
       Company_Name_Role-Title_YYYY-MM-DD.html"""
    base = filename.rsplit('.html', 1)[0] if filename.endswith('.html') else filename
    # Try to extract date from end
    date_m = re.search(r'(\d{4}-\d{2}-\d{2})$', base)
    date = date_m.group(1) if date_m else "2026-04-02"
    if date_m:
        base = base[:date_m.start()].rstrip('_')

    # Split: first part is company, last part is role (with dashes)
    # Handle "Jamie (Yi-Chieh) Cheng" in the middle
    # Pattern: Company_Jamie (Yi-Chieh) Cheng_Role-Title
    name_m = re.search(r'^(.+?)_(?:Jamie \(Yi-Chieh\) Cheng_)?(.+)$', base)
    if name_m:
        company = name_m.group(1).strip()
        role = name_m.group(2).replace('-', ' ').strip()
    else:
        company = base
        role = ""

    return company, role, date


def extract_meta(html, filename):
    m = re.search(r'<!--\s*TAILORED:\s*(.+?)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*-->', html)
    if m:
        company_role = m.group(1).strip()
        date = m.group(2)
        parts = company_role.split(' \u2014 ', 1)
        if len(parts) == 1:
            parts = company_role.split(' — ', 1)
        company = parts[0].strip()
        role = parts[1].strip() if len(parts) > 1 else ""
    else:
        # Fallback: parse from filename
        company, role, date = parse_filename_meta(filename)

    return {
        "company": company,
        "role": role,
        "date": date,
        "pageMargins": extract_page_margins(html)
    }


def extract_header_location(html):
    m = re.search(r'<div class="contact">\s*\n?\s*([^<\n]+)', html)
    if m:
        loc = m.group(1).strip()
        loc = decode_entities(loc)
        # Split on bullet separator and take first part (the location)
        parts = re.split(r'\s*[\u2022\u00b7]\s*', loc)
        loc = parts[0].strip() if parts else loc
        # Remove trailing punctuation
        loc = loc.rstrip(' \u2022\u00b7')
        return loc
    return "Portland, OR (Open to Relocation)"


def extract_summary(html):
    m = re.search(r'<div class="summary">(.*?)</div>', html, re.DOTALL)
    if not m:
        return ""
    text = m.group(1).strip()
    text = convert_kw_spans(text)
    # Keep <b> tags, remove everything else
    text = re.sub(r'<(?!/?b\b)[^>]+>', '', text)
    text = decode_entities(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_keyword_groups(html):
    groups = {}
    for m in re.finditer(r'<span\s+class="leg-(\w+)">(.*?)</span>', html):
        groups[m.group(1)] = decode_entities(m.group(2))
    return groups


def extract_li_attrs(li_tag_str):
    """Parse attributes from an <li ...> opening tag string."""
    attrs = {}
    # class
    m = re.search(r'class="([^"]*)"', li_tag_str)
    if m:
        attrs['classes'] = m.group(1).split()
    else:
        attrs['classes'] = []
    # data-original
    m = re.search(r'data-original="([^"]*)"', li_tag_str)
    if m:
        attrs['data-original'] = decode_entities(m.group(1))
    # data-was
    m = re.search(r'data-was="([^"]*)"', li_tag_str)
    if m:
        attrs['data-was'] = m.group(1)
    # data-jd
    m = re.search(r'data-jd="([^"]*)"', li_tag_str)
    if m:
        attrs['data-jd'] = m.group(1)
    # data-reason
    m = re.search(r'data-reason="([^"]*)"', li_tag_str)
    if m:
        attrs['data-reason'] = decode_entities(m.group(1))
    return attrs


JOB_ID_MAP = {
    'organization development network': 'odn',
    'odn': 'odn',
    'ingenius': 'ingenius',
    'nextgen': 'nextgen',
    'vestas': 'vestas',
    'kronos': 'kronos',
    'superhuman': 'superhuman',
}


def guess_job_id(company):
    cl = company.lower()
    for key, val in JOB_ID_MAP.items():
        if key in cl:
            return val
    return 'unknown'


def extract_experience(html):
    jobs = []
    exp_start = html.find('>Professional Experience<')
    if exp_start == -1:
        return jobs
    edu_start = html.find('>Education<', exp_start)
    if edu_start == -1:
        edu_start = len(html)
    exp_html = html[exp_start:edu_start]

    job_blocks = re.split(r'<div class="job">', exp_html)[1:]

    for block in job_blocks:
        job = {}

        # Title (may contain work sample link)
        title_m = re.search(r'<div class="job-title">(.*?)</div>', block, re.DOTALL)
        if title_m:
            title_html = title_m.group(1).strip()
            ws_m = re.search(r'<a[^>]*class="work-sample"[^>]*href="([^"]+)"', title_html)
            job['workSampleUrl'] = ws_m.group(1) if ws_m else None
            job['title'] = decode_entities(strip_tags(title_html).replace('(Work Sample)', '').strip())
        else:
            job['title'] = ''
            job['workSampleUrl'] = None

        loc_m = re.search(r'<div class="job-location">(.*?)</div>', block)
        job['location'] = decode_entities(strip_tags(loc_m.group(1).strip())) if loc_m else ""

        comp_m = re.search(r'<div class="job-company">(.*?)</div>', block)
        job['company'] = decode_entities(strip_tags(comp_m.group(1).strip())) if comp_m else ""

        dates_m = re.search(r'<div class="job-dates">(.*?)</div>', block)
        job['dates'] = decode_entities(strip_tags(dates_m.group(1).strip())) if dates_m else ""

        job['id'] = guess_job_id(job['company'])

        # Bullets - match each <li...>...</li>
        bullets = []
        for li_m in re.finditer(r'<li([^>]*)>(.*?)</li>', block, re.DOTALL):
            li_tag_attrs = li_m.group(1)
            li_inner = li_m.group(2).strip()
            attrs = extract_li_attrs(li_tag_attrs)

            bullet = {}
            bullet['text'] = clean_bullet_text(li_inner)

            if 'changed' in attrs['classes']:
                bullet['change'] = 'swap'
            elif 'reordered' in attrs['classes']:
                bullet['change'] = 'reorder'
            else:
                bullet['change'] = None

            if 'data-original' in attrs:
                bullet['original'] = attrs['data-original']
            if 'data-was' in attrs:
                bullet['was'] = int(attrs['data-was'])
            if 'data-jd' in attrs:
                bullet['jd'] = [x.strip() for x in attrs['data-jd'].split(',')]
            if 'data-reason' in attrs:
                bullet['reason'] = attrs['data-reason']

            bullets.append(bullet)

        ordered = {
            'id': job['id'],
            'title': job['title'],
            'company': job['company'],
            'location': job['location'],
            'dates': job['dates'],
            'workSampleUrl': job['workSampleUrl'],
            'bullets': bullets
        }
        jobs.append(ordered)

    return jobs


def extract_education(html):
    edus = []
    start = html.find('>Education<')
    if start == -1:
        return edus
    next_sec = html.find('class="section-header"', start + 20)
    if next_sec == -1:
        next_sec = len(html)
    edu_html = html[start:next_sec]

    for block in re.split(r'<div class="edu">', edu_html)[1:]:
        edu = {}
        m = re.search(r'<div class="edu-school">(.*?)</div>', block)
        edu['school'] = decode_entities(strip_tags(m.group(1).strip())) if m else ""
        m = re.search(r'<div class="edu-location">(.*?)</div>', block)
        edu['location'] = decode_entities(strip_tags(m.group(1).strip())) if m else ""
        m = re.search(r'<div class="edu-degree">(.*?)</div>', block)
        edu['degree'] = decode_entities(strip_tags(m.group(1).strip())) if m else ""
        m = re.search(r'<div class="edu-dates">(.*?)</div>', block)
        edu['dates'] = decode_entities(strip_tags(m.group(1).strip())) if m else ""

        bullets = []
        for li_m in re.finditer(r'<li[^>]*>(.*?)</li>', block, re.DOTALL):
            text = clean_bullet_text(li_m.group(1))
            if text:
                bullets.append(text)
        edu['bullets'] = bullets
        edus.append(edu)

    return edus


def extract_simple_list(html, section_name):
    """Extract a simple-list section (Projects, Skills)."""
    items = []
    # Must find section-header div specifically
    # Use regex to find section-header containing the keyword
    start = -1
    for m in re.finditer(r'<div class="section-header">[^<]*' + re.escape(section_name) + r'[^<]*</div>', html):
        start = m.start()
        # Use the last occurrence in case earlier ones are in changelog tables
        # Actually we want the one inside .resume-page, which is the one with the div wrapper
        break  # The regex is specific enough with <div class="section-header">

    if start == -1:
        return items

    # Find next section-header or page-guide
    end = len(html)
    for marker in ['class="section-header"', 'class="page-guide"', '</div><!-- .resume-page -->']:
        pos = html.find(marker, start + 20)
        if pos != -1 and pos < end:
            end = pos

    section_html = html[start:end]

    for li_m in re.finditer(r'<li[^>]*>(.*?)</li>', section_html, re.DOTALL):
        text = li_m.group(1).strip()
        text = re.sub(r'^[\u2022\u00b7]\s*', '', text)
        text = convert_kw_spans(text)
        # Keep <b> tags, strip everything else
        text = re.sub(r'<(?!/?b\b)[^>]+>', '', text)
        text = decode_entities(text)
        text = re.sub(r'\s+', ' ', text).strip()
        if text:
            items.append(text)

    return items


def extract_jd_panel(html):
    """Extract JD panel content."""
    # Find jd-content div
    jd_start = html.find('<div class="jd-content">')
    if jd_start == -1:
        return None
    # Find end of jd-panel
    jd_end = html.find('</div>\n</div>', jd_start + 20)
    if jd_end == -1:
        jd_end = html.find('</div>\r\n</div>', jd_start + 20)
    if jd_end == -1:
        # More forgiving: find the closing of jd-panel
        jd_end = html.find('</div><!-- .split-layout', jd_start)
    if jd_end == -1:
        jd_end = len(html)

    jd_html = html[jd_start:jd_end]
    jd = {}

    # Meta
    meta_m = re.search(r'<div class="jd-meta">(.*?)</div>', jd_html)
    jd['meta'] = decode_entities(strip_tags(meta_m.group(1).strip())) if meta_m else ""

    # Check if section titles exist in the content
    has_sections = '<div class="jd-section-title">' in jd_html

    if has_sections:
        # Structured format with section titles
        sections = []
        parts = re.split(r'<div class="jd-section-title">(.*?)</div>', jd_html)
        for i in range(1, len(parts), 2):
            title = decode_entities(strip_tags(parts[i].strip()))
            content = parts[i + 1] if i + 1 < len(parts) else ""
            section = {"title": title}

            if '<ul>' in content or re.search(r'<li[^>]*>', content):
                section['type'] = 'list'
                section['items'] = extract_jd_list_items(content)
            else:
                section['type'] = 'paragraph'
                text = convert_kw_spans(content)
                text = strip_tags(text)
                text = decode_entities(text)
                text = re.sub(r'\s+', ' ', text).strip()
                section['content'] = text

            sections.append(section)
        jd['sections'] = sections
    else:
        # Flat format (Aurora-style): paragraphs with marks
        section = {"title": "Job Description", "type": "mixed", "items": []}
        # Extract each <p> or <mark> with jd-hl
        for p_m in re.finditer(r'<p>(.*?)</p>', jd_html, re.DOTALL):
            p_content = p_m.group(1).strip()
            # Check if it contains a jd-hl mark
            mark_m = re.search(r'<mark\s+class="jd-hl\s+(jd-\w+)"\s+id="(\w+)">(.*?)</mark>', p_content, re.DOTALL)
            if mark_m:
                item = parse_jd_mark(mark_m, p_content)
                section['items'].append(item)
            else:
                # Plain paragraph
                text = convert_kw_spans(p_content)
                text = strip_tags(text)
                text = decode_entities(text)
                text = re.sub(r'\s+', ' ', text).strip()
                if text and text != jd['meta']:
                    section['items'].append({"text": text})

        jd['sections'] = [section]

    return jd


def parse_jd_mark(mark_match, full_content):
    """Parse a <mark class="jd-hl jd-swap" id="jd1">...</mark>."""
    change_class = mark_match.group(1)
    change_map = {'jd-swap': 'swap', 'jd-order': 'reorder', 'jd-word': 'word'}

    mark_text = mark_match.group(3)
    mark_text = convert_kw_spans(mark_text)
    mark_text = strip_tags(mark_text)
    mark_text = decode_entities(mark_text)
    mark_text = re.sub(r'^[\u2022\u00b7]\s*', '', mark_text).strip()
    mark_text = re.sub(r'\s+', ' ', mark_text)

    item = {
        'id': mark_match.group(2),
        'changeType': change_map.get(change_class, change_class),
        'text': mark_text
    }

    reason_m = re.search(r'<span class="jd-reason">[^<]*?(?:\u2192|->|&rarr;)\s*(.*?)</span>', full_content)
    if reason_m:
        item['reason'] = decode_entities(reason_m.group(1).strip())

    return item


def extract_jd_list_items(content):
    """Extract items from a JD list section."""
    items = []
    for li_m in re.finditer(r'<li[^>]*>(.*?)</li>', content, re.DOTALL):
        li_content = li_m.group(1).strip()
        mark_m = re.search(r'<mark\s+class="jd-hl\s+(jd-\w+)"\s+id="(\w+)">(.*?)</mark>', li_content, re.DOTALL)
        if mark_m:
            item = parse_jd_mark(mark_m, li_content)
            items.append(item)
        else:
            text = convert_kw_spans(li_content)
            text = strip_tags(text)
            text = decode_entities(text)
            text = re.sub(r'^[\u2022\u00b7]\s*', '', text).strip()
            text = re.sub(r'\s+', ' ', text)
            if text:
                items.append({"text": text})
    return items


def extract_changelog(html):
    """Extract changelog from pane-changes or change-log table, handling <\\td> and </td>."""
    changes = []

    # Try new format first (pane-changes), then old format (change-log)
    pane_start = html.find('id="pane-changes"')
    if pane_start == -1:
        pane_start = html.find('id="change-log"')
    if pane_start == -1:
        return changes

    # Find end of the div (look for </div> after the table)
    # Find the closing </table> first, then the next </div>
    table_end = html.find('</table>', pane_start + 20)
    if table_end == -1:
        return changes
    pane_end = table_end + len('</table>')
    pane_html = html[pane_start:pane_end]

    # Normalize <\td> to </td>
    pane_html = pane_html.replace('<\\td>', '</td>')
    pane_html = pane_html.replace('<\td>', '</td>')

    # Match table rows (skip header row with <th>)
    rows = re.findall(
        r'<tr>\s*<td>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>',
        pane_html, re.DOTALL
    )

    type_map = {
        'bullet swap': 'swap',
        'reorder': 'reorder',
        'word swap': 'word',
    }

    for row in rows:
        location = strip_tags(row[0]).strip()
        type_text = strip_tags(row[1]).strip()
        type_text = re.sub(r'^[^\w]*', '', type_text).strip()  # Remove emoji prefix
        change_type = type_map.get(type_text, type_text)

        before = decode_entities(strip_tags(row[2]).strip())
        after = decode_entities(strip_tags(row[3]).strip())
        why = decode_entities(strip_tags(row[4]).strip())

        changes.append({
            "location": location,
            "type": change_type,
            "before": before,
            "after": after,
            "why": why
        })

    return changes


def process_file(filepath):
    html = read_file(filepath)
    filename = os.path.basename(filepath)

    return {
        "meta": extract_meta(html, filename),
        "header": {"location": extract_header_location(html)},
        "summary": extract_summary(html),
        "keywordGroups": extract_keyword_groups(html),
        "experience": extract_experience(html),
        "education": extract_education(html),
        "projects": extract_simple_list(html, "Projects"),
        "skills": extract_simple_list(html, "Skills"),
        "jd": extract_jd_panel(html),
        "changeLog": extract_changelog(html)
    }


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # HTML files may be in legacy_html/ subdirectory or in base_dir
    html_dir = os.path.join(base_dir, 'legacy_html')
    if not os.path.isdir(html_dir) or not any(f.endswith('.html') for f in os.listdir(html_dir)):
        html_dir = base_dir
    html_files = sorted([f for f in os.listdir(html_dir) if f.endswith('.html')])

    print(f"Found {len(html_files)} HTML files")

    for html_file in html_files:
        filepath = os.path.join(html_dir, html_file)
        json_file = html_file.rsplit('.html', 1)[0] + '.json'
        json_path = os.path.join(base_dir, json_file)  # JSON goes in parent dir

        print(f"\nProcessing: {html_file}")

        try:
            data = process_file(filepath)

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            exp_count = len(data['experience'])
            bullet_count = sum(len(j['bullets']) for j in data['experience'])
            jd_sections = len(data.get('jd', {}).get('sections', [])) if data.get('jd') else 0
            jd_items = sum(len(s.get('items', [])) for s in data.get('jd', {}).get('sections', [])) if data.get('jd') else 0
            changelog_count = len(data['changeLog'])
            proj_count = len(data['projects'])
            skill_count = len(data['skills'])

            print(f"  -> {json_file}")
            print(f"    {exp_count} jobs, {bullet_count} bullets, {proj_count} projects, {skill_count} skills")
            print(f"    JD: {jd_sections} sections, {jd_items} items | Changelog: {changelog_count} entries")

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    main()
