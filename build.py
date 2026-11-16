#!/usr/bin/env python3
"""
Karibu TUM static site generator.

Reads data/content.json and writes every page as plain static HTML
(no server, no framework). Edit the JSON, run `python3 build.py`, done.

Image slots: set a path in the JSON (e.g. "image": "assets/images/student-life/clubs.jpg")
and the card/hero/gallery shows it automatically if the file exists. Nothing renders a
broken image when a file is missing; a consistent icon visual is used instead.
"""
import html
import json
import os
import re
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(ROOT, "data", "content.json"), encoding="utf-8"))
S = D["site"]


# ---------------------------------------------------------------- helpers
def e(s):
    """Escape for HTML and use typographic apostrophes in visible text."""
    return html.escape(str(s), quote=True).replace("&#x27;", "\u2019")


def exists(rel):
    return bool(rel) and os.path.exists(os.path.join(ROOT, rel))


def find_first(folder, stems):
    d = os.path.join(ROOT, folder)
    if not os.path.isdir(d):
        return None
    for f in sorted(os.listdir(d)):
        name, ext = os.path.splitext(f)
        if name.lower() in stems and ext.lower() in (".svg", ".png", ".webp", ".jpg", ".jpeg"):
            return f"{folder}/{f}"
    return None


ICONS = {
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "trophy": '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>',
    "megaphone": '<path d="m3 11 18-5v12L3 14v-3z"/><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6"/>',
    "message": '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
    "home": '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
    "health": '<path d="M11 2a2 2 0 0 0-2 2v5H4a2 2 0 0 0-2 2v2c0 1.1.9 2 2 2h5v5c0 1.1.9 2 2 2h2a2 2 0 0 0 2-2v-5h5a2 2 0 0 0 2-2v-2a2 2 0 0 0-2-2h-5V4a2 2 0 0 0-2-2z"/>',
    "headset": '<path d="M3 11h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-5Zm0 0a9 9 0 1 1 18 0m0 0v5a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3Z"/><path d="M21 16v2a4 4 0 0 1-4 4h-5"/>',
    "arrow": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "external": '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    "chevron": '<path d="m6 9 6 6 6-6"/>',
    "menu": '<line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/>',
    "close": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "mail": '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    "phone": '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/>',
    "pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "calendar": '<rect width="18" height="18" x="3" y="4" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "bell": '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
    "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>',
    "file": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/>',
    "user": '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "image": '<rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.09-3.09a2 2 0 0 0-2.82 0L6 21"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4M12 17h.01"/>',
    "send": '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
    "star": '<path d="m12 2 3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>',
}


def ic(name, cls=""):
    return f'<svg class="icon {cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{ICONS[name]}</svg>'


def L(root, path="", anchor=""):
    """Internal link: root-relative prefix + folder/index.html (works on file:// too)."""
    target = root + (path.rstrip("/") + "/index.html" if path else "index.html")
    return target + (("#" + anchor) if anchor else "")


def phone_link(cls=""):
    return f'<a class="{cls}" href="tel:{S["phone_tel"]}">{ic("phone")}<span>{e(S["phone_display"])}</span></a>'


def mail_link(addr, cls=""):
    return f'<a class="{cls}" href="mailto:{addr}">{ic("mail")}<span>{e(addr)}</span></a>'


def plain_mail(addr):
    return f'<a href="mailto:{addr}">{e(addr)}</a>'


def plain_tel():
    return f'<a href="tel:{S["phone_tel"]}">{e(S["phone_display"])}</a>'


def media(item, root, ratio_cls="", alt_override=None):
    """Image if the file exists, otherwise consistent icon visual."""
    if exists(item.get("image")):
        return f'<img src="{root}{item["image"]}" alt="{e(alt_override if alt_override is not None else item.get("image_alt", ""))}" loading="lazy">'
    return f'<div class="visual" aria-hidden="true">{ic(item.get("icon", "image"))}</div>'


def empty(icon, title, text, link=None):
    extra = f'<a class="text-link" href="{link[1]}">{e(link[0])} {ic("arrow")}</a>' if link else ""
    return (f'<div class="empty" role="status"><span class="chip">{ic(icon)}</span>'
            f'<h4>{e(title)}</h4><p>{e(text)}</p>{extra}</div>')


def section_head(title, lead="", action=None, centered=False):
    act = f'<a class="btn btn-soft" href="{action[1]}">{e(action[0])} {ic("arrow")}</a>' if action else ""
    cls = " centered" if centered else ""
    lead_html = f"<p>{e(lead)}</p>" if lead else ""
    return (f'<div class="section-head{cls}"><div><span class="gold-bar" aria-hidden="true"></span>'
            f'<h2>{e(title)}</h2>{lead_html}</div>{act}</div>')


# ---------------------------------------------------------------- components
def life_card(item, root):
    href = L(root, f"student-life/{item['slug']}")
    return (f'<article class="card"><div class="card-media"><div class="card-media-inner">{media(item, root)}</div>'
            f'<span class="card-badge" aria-hidden="true">{ic(item["icon"])}</span></div>'
            f'<div class="card-body"><h3><a href="{href}">{e(item["title"])}</a></h3>'
            f'<p>{e(item["short"])}</p>'
            f'<span class="card-action" aria-hidden="true">View details {ic("arrow")}</span></div></article>')


def service_card(item, root):
    href = L(root, f"student-services/{item['slug']}")
    return (f'<article class="service-card"><span class="chip" aria-hidden="true">{ic(item["icon"])}</span>'
            f'<h3><a href="{href}">{e(item["title"])}</a></h3><p>{e(item["short"])}</p>'
            f'<span class="go" aria-hidden="true">{ic("arrow")}</span></article>')


def static_card(title, desc, icon="star"):
    return (f'<article class="service-card"><span class="chip" aria-hidden="true">{ic(icon)}</span>'
            f'<h3>{e(title)}</h3><p>{e(desc)}</p></article>')


def portrait(person, root, big=False):
    if exists(person.get("portrait")):
        return f'<div class="portrait"><img src="{root}{person["portrait"]}" alt="{e(person.get("portrait_alt", ""))}"></div>'
    return (f'<div class="portrait" role="img" aria-label="{e(person["name"])}, {e(person["role"])}">'
            f'<div class="avatar"><span class="initials" aria-hidden="true">{e(person["initials"])}</span></div></div>')


def staff_card(p, root):
    contact = ""
    if p.get("email"):
        contact += mail_link(p["email"])
    if p.get("phone"):
        contact += f'<a href="tel:{re.sub(r"[^+0-9]", "", p["phone"])}">{ic("phone")}<span>{e(p["phone"])}</span></a>'
    contact = f'<div class="contact">{contact}</div>' if contact else ""
    return (f'<article class="staff-card">{portrait(p, root)}<div class="staff-body">'
            f'<h3>{e(p["name"])}</h3><p class="role">{e(p["role"])}</p>{contact}</div></article>')


def fmt_date(iso, fmt):
    try:
        return datetime.fromisoformat(iso).strftime(fmt)
    except Exception:
        return iso


def event_row(ev, root):
    d = ev.get("date", "")
    meta = ""
    if ev.get("date_label"):
        meta += f'<span>{ic("calendar")}{e(ev["date_label"])}</span>'
    if ev.get("time"):
        meta += f'<span>{ic("clock")}{e(ev["time"])}</span>'
    if ev.get("venue"):
        meta += f'<span>{ic("pin")}{e(ev["venue"])}</span>'
    link = ""
    if ev.get("link"):
        ext = ev["link"].startswith("http")
        link = (f'<a class="text-link" href="{ev["link"]}"' + (' target="_blank" rel="noopener"' if ext else "") +
                f'>{e(ev.get("link_label", "Event details"))} {ic("external" if ext else "arrow")}'
                + ('<span class="visually-hidden"> (opens in a new tab)</span>' if ext else "") + "</a>")
    img = f'<img src="{root}{ev["image"]}" alt="{e(ev.get("image_alt", ""))}" loading="lazy">' if exists(ev.get("image")) else ""
    date_badge = (f'<div class="date-badge"><span class="m">{e(fmt_date(d, "%b"))}</span>'
                  f'<span class="d">{e(fmt_date(d, "%d"))}</span>'
                  f'<span class="visually-hidden">{e(fmt_date(d, "%A %d %B %Y"))}</span></div>'
                  if d else "")
    row_class = "event-row" if d else "event-row event-row-no-date"
    return (f'<li class="{row_class}">{date_badge}'
            f'<div><h4>{e(ev["title"])}</h4><div class="event-meta">{meta}</div>'
            f'{"<p>" + e(ev["description"]) + "</p>" if ev.get("description") else ""}{link}{img}</div></li>')


def event_card(ev, root):
    if exists(ev.get("image")):
        media = f'<img src="{root}{ev["image"]}" alt="{e(ev.get("image_alt", ""))}" loading="lazy">'
    else:
        media = f'<div class="event-card-art" aria-hidden="true">{ic(ev.get("icon", "calendar"))}</div>'
    letter = ev.get("letter")
    if exists(letter):
        action = (f'<a class="btn btn-primary" href="{root}{letter}" download '
                  f'aria-label="Download signed event letter for {e(ev["title"])}">'
                  f'{ic("download")}Download</a>')
        status = ""
    else:
        action = (f'<button class="btn btn-primary" type="button" disabled '
                  f'aria-label="Download letter for {e(ev["title"])}; letter coming soon">'
                  f'{ic("download")}Download</button>')
        status = '<span class="event-letter-status">Letter coming soon</span>'
    return (f'<article class="event-card"><div class="event-card-media">{media}</div>'
            f'<div class="event-card-body"><h3>{e(ev["title"])}</h3>'
            f'<div class="event-card-meta"><span>{ic("calendar")}{e(ev.get("date_label", "Date in signed letter"))}</span>'
            f'<span>{ic("user")}Organized by {e(ev.get("organizer", "TUM"))}</span></div>'
            f'<div class="event-card-action">{action}{status}</div></div></article>')


def notice_row(a):
    imp = a.get("important")
    tag = f'<span class="tag important">{ic("alert")}Important</span>' if imp else ""
    cat = f'<span class="tag">{e(a["category"])}</span>' if a.get("category") else ""
    link = ""
    if a.get("link"):
        ext = a["link"].startswith("http")
        link = (f'<a class="text-link" href="{a["link"]}"' + (' target="_blank" rel="noopener"' if ext else "") +
                f'>{e(a.get("link_label", "Read more"))} {ic("external" if ext else "arrow")}'
                + ('<span class="visually-hidden"> (opens in a new tab)</span>' if ext else "") + "</a>")
    return (f'<li class="notice{" important" if imp else ""}">{ic("bell")}<div>'
            f'<div class="meta">{tag}{cat}<time datetime="{e(a.get("date", ""))}">{e(fmt_date(a.get("date", ""), "%d %B %Y"))}</time></div>'
            f'<h4>{e(a["title"])}</h4>{"<p>" + e(a["summary"]) + "</p>" if a.get("summary") else ""}{link}</div></li>')


def resource_row(r):
    meta = " · ".join(x for x in [r.get("file_type"), r.get("size")] if x)
    return (f'<li class="resource-row"><span class="chip" aria-hidden="true">{ic("file")}</span>'
            f'<div><h4>{e(r["title"])}</h4><p>{e(r.get("description", ""))}{(" (" + e(meta) + ")") if meta else ""}</p></div>'
            f'<a class="btn btn-secondary" href="{r["href"]}" download>{ic("download")}Download'
            f'<span class="visually-hidden"> {e(r["title"])}{(", " + e(meta)) if meta else ""}</span></a></li>')


def gallery(items, root, subject):
    if not items:
        return empty("image", "No photographs yet", f"Photographs of {subject} will appear here once they are added.")
    figs = ""
    for g in items:
        if not exists(g.get("src")):
            continue
        src = root + g["src"]
        figs += (f'<figure><button type="button" data-lightbox data-src="{src}" data-alt="{e(g.get("alt", ""))}" data-caption="{e(g.get("caption", ""))}">'
                 f'<img src="{src}" alt="{e(g.get("alt", ""))}" loading="lazy"><span class="visually-hidden">Enlarge image</span></button>'
                 f'{"<figcaption>" + e(g["caption"]) + "</figcaption>" if g.get("caption") else ""}</figure>')
    if not figs:
        return empty("image", "No photographs yet", f"Photographs of {subject} will appear here once they are added.")
    return f'<div class="gallery">{figs}</div>'


def fact(icon, label, value_html):
    return f'<div class="fact">{ic(icon)}<div><dt>{e(label)}</dt><dd>{value_html}</dd></div></div>'


def pending(text):
    return f'<em class="pending">{e(text)}</em>'


def cta_band(title, text, primary, secondary=None):
    sec = f'<a class="btn btn-outline-light" href="{secondary[1]}">{e(secondary[0])}</a>' if secondary else ""
    return (f'<div class="cta-wrap"><div class="container"><section class="cta on-dark" aria-labelledby="cta-h"><div>'
            f'<h2 id="cta-h">{e(title)}</h2><p>{e(text)}</p></div><div class="btn-row">'
            f'<a class="btn btn-gold" href="{primary[1]}">{e(primary[0])} {ic("arrow")}</a>{sec}</div></section></div></div>')


SWOOSH = ('<svg class="hero-swoosh" viewBox="0 0 1440 120" preserveAspectRatio="none" aria-hidden="true" focusable="false">'
          '<path fill="#D89837" d="M0 78 C220 30 430 34 640 84 L640 120 L0 120 Z"/>'
          '<path fill="#0C7C40" d="M470 120 C760 56 1080 34 1440 52 L1440 120 Z"/>'
          '<path fill="#FFFFFF" d="M0 112 C300 86 640 118 980 104 C1180 96 1330 92 1440 100 L1440 120 L0 120 Z"/></svg>')


def hero(h1, intro, root, tagline="", actions="", aside="", photo=None, crumbs="", background_photo=None, photo_alt=""):
    has_photo = bool(photo)
    cls = ("hero" + (" has-aside" if aside and not has_photo else "") +
           (" has-photo" if has_photo else "") +
           (" homepage-hero" if background_photo else ""))
    photo_html = f'<div class="hero-photo"><img src="{root}{photo}" alt="{e(photo_alt or "Photograph of " + h1)}"></div>' if has_photo else ""
    background_html = (f'<div class="hero-background" aria-hidden="true"><img src="{root}{background_photo}" alt=""></div>'
                       if background_photo else "")
    aside_html = aside if (aside and not has_photo) else ""
    tag = f'<p class="tagline">{e(tagline)}</p>' if tagline else ""
    return (f'<section class="{cls}" aria-labelledby="page-title">{background_html}{photo_html}{SWOOSH}'
            f'<div class="container hero-inner"><div class="hero-copy">{crumbs}<span class="gold-bar" aria-hidden="true"></span>'
            f'<h1 id="page-title">{e(h1)}</h1>{tag}<p class="intro">{e(intro)}</p>'
            f'<div class="btn-row">{actions}</div></div>{aside_html}</div></section>')


def breadcrumbs(root, trail):
    items = ""
    for i, (label, href) in enumerate(trail):
        if i == len(trail) - 1:
            items += f'<li aria-current="page">{e(label)}</li>'
        else:
            items += f'<li><a href="{href}">{e(label)}</a></li>'
    return f'<nav class="breadcrumbs" aria-label="Breadcrumb"><ol>{items}</ol></nav>'


# ---------------------------------------------------------------- layout
LOGO = "assets/images/TUM logo.png" if exists("assets/images/TUM logo.png") else None


def nav_html(root, active):
    life = D["student_life"]
    svc = D["student_services"]

    def sub(links_html, sid, label):
        return (f'<button class="sub-toggle" type="button" aria-expanded="false" aria-controls="{sid}">'
                f'{ic("chevron")}<span class="visually-hidden">Show {e(label)} pages</span></button>'
                f'<ul class="submenu" id="{sid}" hidden>{links_html}</ul>')

    def a(label, href):
        return f'<li><a href="{href}">{e(label)}</a></li>'

    def cur(key):
        return ' aria-current="page"' if active == key else ""

    dean_sub = "".join([a("About the Dean", L(root, "deans-office", "about-dean")),
                        a("Dean's Office services", L(root, "deans-office", "services")),
                        a("Staff", L(root, "deans-office", "staff"))])
    life_sub = ('<li class="group-label" role="presentation">Student Life</li>' +
                "".join(a(x["title"], L(root, f"student-life/{x['slug']}")) for x in life) +
                '<li class="sep" role="presentation"></li><li class="group-label" role="presentation">Student Services</li>' +
                "".join(a(x["title"], L(root, f"student-services/{x['slug']}")) for x in svc))
    news_sub = "".join([a("Events", L(root, "announcements-events", "events")),
                        a("Announcements", L(root, "announcements-events", "announcements")),
                        a("Resources download", L(root, "announcements-events", "resources"))])
    contact_sub = "".join([a("Contact the Dean's Office", L(root, "contact-support", "contact")),
                           a("Send an enquiry", L(root, "contact-support", "enquiry")),
                           a("Guidance & Counselling", L(root, "student-services/guidance-counselling"))])

    home_sub = "".join([
        a("Welcome", L(root, "", "welcome")),
        a("Student Life at TUM", L(root, "", "student-life")),
        a("About the Dean", L(root, "", "about-dean")),
        a("Announcements & Events", L(root, "", "announcements-events")),
    ])

    return f'''<nav class="primary-nav" id="primary-nav" aria-label="Primary">
<ul>
<li class="nav-item"><a class="nav-link"{cur("home")} href="{L(root)}">Homepage</a>{sub(home_sub, "sub-home", "Homepage")}</li>
<li class="nav-item"><a class="nav-link" href="{L(root, "deans-office")}"{cur("dean")}>{e("Dean's Office")}</a>{sub(dean_sub, "sub-dean", "Dean's Office")}</li>
<li class="nav-item"><a class="nav-link" href="{L(root, "student-life")}"{cur("life")}>Student Life</a>{sub(life_sub, "sub-life", "Student Life")}</li>
<li class="nav-item"><a class="nav-link" href="{L(root, "announcements-events")}"{cur("news")}>Announcements &amp; Events</a>{sub(news_sub, "sub-news", "Announcements & Events")}</li>
<li class="nav-item"><a class="nav-link" href="{L(root, "contact-support")}"{cur("contact")}>Contact &amp; Support</a>{sub(contact_sub, "sub-contact", "Contact & Support")}</li>
<li class="nav-item"><a class="nav-link nav-main" href="{S["main_site"]}" target="_blank" rel="noopener">{ic("home")}Main site{ic("external")}<span class="visually-hidden"> (Technical University of Mombasa, opens in a new tab)</span></a></li>
</ul></nav>'''.replace("<li class=\"group-label\" role=\"presentation\">", "<li class=\"group-label\" role=\"presentation\">")


def header_html(root, active):
    if LOGO:
        brand = f'<img class="brand-logo" src="{root}{LOGO}" alt="Technical University of Mombasa logo">'
    else:
        # Text lockup only. The official logo has not been supplied; do not redraw it.
        brand = (f'<span class="brand-text"><span class="uni">{e(S["university"])}</span>'
                 f'<span class="portal">{e(S["name"])}</span></span>')
    return f'''    <div class="utility" id="top"><div class="container">
{mail_link(S["email_general"])}
{phone_link()}
<span class="addr">{ic("pin")}<span>{e(S["address"])} &middot; {e(S["po_box"])}</span></span>
</div></div>
<header class="site-header"><div class="container header-inner">
<a class="brand" href="{L(root)}" aria-label="{e(S["name"])} homepage">{brand}</a>
<button class="nav-toggle" type="button" aria-expanded="false" aria-controls="primary-nav">{ic("menu", "icon-open")}{ic("close", "icon-close")}<span class="toggle-label">Menu</span></button>
{nav_html(root, active)}
</div></header>'''


def footer_html(root):
    def li(label, href, ext=False):
        t = ' target="_blank" rel="noopener"' if ext else ""
        extra = f'{ic("external")}<span class="visually-hidden"> (opens in a new tab)</span>' if ext else ""
        return f'<li><a href="{href}"{t}>{e(label)}{(" " + extra) if ext else ""}</a></li>'

    main = S["main_site"]
    phones = (
        ("+254 41 2492222", "+254412492222"),
        ("+254 733 955377", "+254733955377"),
        ("+254 20 8095368", "+254208095368"),
    )
    phone_links = "".join(
        f'<a href="tel:{number}">{ic("phone")}<span>{e(label)}</span></a>'
        for label, number in phones
    )
    social_icons = (
        '<span class="social-icon facebook" role="img" aria-label="Facebook">f</span>'
        '<span class="social-icon x" role="img" aria-label="X">X</span>'
        '<span class="social-icon youtube" role="img" aria-label="YouTube">'
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M23 7.2a3 3 0 0 0-2.1-2.1C19 4.6 12 4.6 12 4.6s-7 0-8.9.5A3 3 0 0 0 1 7.2 31 31 0 0 0 .5 12a31 31 0 0 0 .5 4.8 3 3 0 0 0 2.1 2.1c1.9.5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 0 0 2.1-2.1A31 31 0 0 0 23.5 12a31 31 0 0 0-.5-4.8ZM9.7 15.3V8.7l5.8 3.3-5.8 3.3Z"/></svg></span>'
        '<span class="social-icon linkedin" role="img" aria-label="LinkedIn">in</span>'
        '<span class="social-icon instagram" role="img" aria-label="Instagram">'
        '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle class="instagram-dot" cx="17.5" cy="6.8" r="1"/></svg></span>'
        '<span class="social-icon tiktok" role="img" aria-label="TikTok">&#9835;</span>'
    )
    return f'''<footer class="site-footer on-dark"><div class="container">
<div class="footer-top">
<div class="footer-col footer-contact-col"><h2>Contact</h2>
<div class="footer-contact">
<span>{ic("pin")}<span>{e(S["address"])}<br>{e(S["po_box"])}</span></span>
{phone_links}
{mail_link(S["email_general"])}
</div>
<h3 class="footer-follow-title">Follow the University</h3>
<div class="footer-social" aria-label="University social media">{social_icons}</div>
</div>
<div class="footer-col"><h2>Study at TUM</h2><ul>
{li("All Programmes", main, True)}
{li("Application Requirements", main, True)}
{li("How to Apply", main, True)}
{li("Admission Documents", main, True)}
{li("Fee Structures", main, True)}
{li("Funding & Scholarships", main, True)}
</ul></div>
<div class="footer-col"><h2>The University</h2><ul>
{li("About TUM", main, True)}
{li("Governance & Leadership", main, True)}
{li("Schools & Faculties", main, True)}
{li("Our Campuses", main, True)}
{li("Karibu TUM", L(root))}
{li("Research & Innovation", main, True)}
{li("Careers at TUM", main, True)}
{li("Contact Us", L(root, "contact-support"))}
</ul></div>
<div class="footer-col"><h2>Important Links</h2><ul>
{li("Multidisciplinary Journal", main, True)}
{li("Academic Calendar", main, True)}
{li("Tenders & Procurement", main, True)}
{li("Service Delivery Charter", main, True)}
{li("FAQs", main, True)}
</ul></div>
<div class="footer-col"><h2>Portals &amp; Resources</h2><ul>
{li("Student Portal (TUMMIS)", main, True)}
{li("E-Learning", main, True)}
{li("Online Clearance", main, True)}
{li("Staff Intranet", main, True)}
{li("Staff Portal", main, True)}
{li("Industrial Attachment", main, True)}
{li("Library", main, True)}
</ul></div>
</div>
<div class="footer-bottom"><span>&copy; 2026 {e(S["university"])}. All Rights Reserved.</span>
<nav aria-label="Legal and accessibility">
<ul>
<li><a href="{main}" target="_blank" rel="noopener">Accessibility</a></li>
<li><a href="{main}" target="_blank" rel="noopener">Terms &amp; Conditions</a></li>
<li><a href="{main}" target="_blank" rel="noopener">Privacy and Cookies</a></li>
<li><span>Cookies settings</span></li>
</ul>
</nav></div>
</div></footer>
<a class="back-to-top" href="#top" aria-label="Back to top">{ic("chevron")}</a>'''


FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
           "%3Ccircle cx='32' cy='32' r='30' fill='%230C7C40'/%3E%3Ccircle cx='46' cy='18' r='7' fill='%23D89837'/%3E%3C/svg%3E")


def page(rel_path, title, desc, active, body, lightbox=False):
    depth = rel_path.count("/")
    root = "../" * depth
    lb = ('<dialog class="lightbox" id="lightbox" aria-label="Enlarged photograph"><button type="button" class="btn btn-outline-light close">'
          'Close</button><img src="" alt=""><p></p></dialog>') if lightbox else ""
    out = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#0C7C40">
<link rel="icon" href="{FAVICON}">
<link rel="stylesheet" href="{root}assets/css/styles.css">
</head>
<body>
<a class="skip-link" href="#main">Skip to main content</a>
{header_html(root, active)}
<main id="main" tabindex="-1">
{body(root) if callable(body) else body}
</main>
{footer_html(root)}
{lb}
<script src="{root}assets/js/main.js" defer></script>
</body>
</html>
'''
    out = re.sub(r"(?<=[A-Za-z])'(?=[a-z])", "\u2019", out)
    path = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote", rel_path)


# ---------------------------------------------------------------- shared blocks
def events_block(root, limit=None, home=False):
    evs = sorted(D["events"], key=lambda x: x.get("date", ""))
    if limit:
        evs = evs[:limit]
    if not evs:
        return empty("calendar", "No events scheduled yet",
                     "Upcoming student events will be listed here as soon as they are confirmed.",
                     ("Ask the Dean's Office about events", L(root, "contact-support", "enquiry")))
    return f'<ul class="event-list">{"".join(event_row(x, root) for x in evs)}</ul>'


def event_cards_block(root):
    evs = D["events"]
    if not evs:
        return empty("calendar", "No events scheduled yet",
                     "Upcoming student events will be listed here as soon as they are confirmed.",
                     ("Ask the Dean's Office about events", L(root, "contact-support", "enquiry")))
    return f'<div class="grid grid-3 event-card-grid">{"".join(event_card(ev, root) for ev in evs)}</div>'


def notices_block(root, limit=None):
    ann = sorted(D["announcements"], key=lambda x: x.get("date", ""), reverse=True)
    if limit:
        ann = ann[:limit]
    if not ann:
        return empty("bell", "No announcements yet",
                     "Notices from the Dean's Office will be posted here. Check back soon.")
    return f'<ul class="notice-list">{"".join(notice_row(x) for x in ann)}</ul>'


def dean_about(root, heading_level_h2=True, full=False):
    dn = D["dean"]
    msg = dn.get("message")
    message_paragraphs = dn.get("message_paragraphs", [])
    if message_paragraphs:
        message_html = "".join(f'<p>{e(paragraph)}</p>' for paragraph in message_paragraphs)
        signature = dn.get("message_signature")
        attribution = dn.get("message_attribution")
        institution = dn.get("message_institution")
        if signature or attribution or institution:
            signature_html = f'<strong>{e(signature)}</strong>' if signature else ""
            if attribution:
                signature_html += f'<br>{e(attribution)}'
            if institution:
                signature_html += f'<br>{e(institution)}'
            message_html += f'<p class="message-signature">{signature_html}</p>'
        msg_html = f'<div class="message-box"><h3>A message from the Acting Dean</h3>{message_html}</div>'
    elif msg:
        msg_html = f'<div class="message-box"><h3>A message from the Dean</h3><p>{e(msg)}</p></div>'
    else:
        msg_html = ('<div class="message-box"><h3>A message from the Dean</h3>'
                    '<p>The Dean\'s message will be published here once it has been approved.</p></div>')
    return dn, msg_html


# ---------------------------------------------------------------- pages
def build_home():
    def body(root):
        life = D["student_life"]
        svc = D["student_services"]
        dn, msg_html = dean_about(root)
        help_items = "".join(
            f'<li><a href="{L(root, "student-services/" + s["slug"])}"><span class="chip">{ic(s["icon"])}</span>{e(s["title"])}<span class="go">{ic("arrow")}</span></a></li>'
            for s in svc)
        aside = (f'<aside class="help-panel" aria-labelledby="help-h"><h2 id="help-h">Find a student service</h2>'
                 f'<p>Support for your health, wellbeing and accommodation.</p><ul class="help-list">{help_items}</ul>'
                 f'<div class="help-contact">{mail_link(S["email_dean"])}{phone_link()}</div></aside>')
        actions = (f'<a class="btn btn-primary" href="{L(root, "student-life")}">Explore Student Life {ic("arrow")}</a>'
                   f'<a class="btn btn-secondary" href="{L(root, "student-life", "student-services")}">Find a Student Service</a>'
                   f'<a class="btn btn-secondary" href="{L(root, "contact-support")}">Contact &amp; Support</a>')
        intro = ("Karibu TUM is the Student Affairs and Welfare Portal of Technical University of Mombasa: "
                 "your gateway to student welfare, campus life and support services.")
        h = hero("Welcome to Karibu TUM", intro, root, tagline=S["tagline"], actions=actions, aside=aside,
                 background_photo="assets/images/tum gate A.jpg")
        h = h.replace('<section class="hero', '<section id="welcome" class="hero', 1)

        s1 = (f'<section class="section" id="student-life" aria-labelledby="life-h"><div class="container">'
              f'<div class="section-head"><div><span class="gold-bar" aria-hidden="true"></span><h2 id="life-h">Student Life at TUM</h2>'
              f'<p>Get involved, build friendships and grow your talents.</p></div>'
              f'<a class="btn btn-soft" href="{L(root, "student-life")}">Explore Student Life {ic("arrow")}</a></div>'
              f'<div class="grid grid-3">{"".join(life_card(x, root) for x in life)}</div></div></section>')

        mini = "".join(f'<a href="{L(root, "student-services/" + s["slug"])}">{ic(s["icon"])}<span>{e(s["title"])}</span></a>' for s in svc)
        s2 = (f'<section class="section section-green" id="about-dean" aria-labelledby="dean-h"><div class="container"><div class="dean-grid">'
              f'{portrait(dn, root)}'
              f'<div class="dean-copy"><span class="gold-bar" aria-hidden="true"></span><h2 id="dean-h">About the Acting Dean</h2>'
              f'<p class="dean-name">{e(dn["name"])}</p><p class="dean-role">{e(dn["role"])}</p>'
              f'<p>{e(dn["summary"])}</p>'
              f'<a class="btn btn-primary" href="{L(root, "deans-office", "about-dean")}">Learn more about the Dean {ic("arrow")}</a></div>'
              f'<div class="side-panel"><h3>{e("Dean's Office services")}</h3><p>Access key services and support.</p>'
              f'<div class="mini-services">{mini}</div>'
              f'<a class="text-link" href="{L(root, "deans-office", "services")}">View all services {ic("arrow")}</a></div>'
              f'</div></div></section>')

        s3 = (f'<section class="section" id="announcements-events" aria-labelledby="news-h"><div class="container">'
              f'<div class="section-head"><div><span class="gold-bar" aria-hidden="true"></span><h2 id="news-h">Announcements &amp; Events</h2>'
              f'<p>Stay informed and never miss an important update.</p></div>'
              f'<a class="btn btn-secondary" href="{L(root, "announcements-events")}">View all {ic("arrow")}</a></div>'
              f'<div class="two-col">'
              f'<section class="panel" aria-labelledby="ev-h"><div class="panel-head"><h3 id="ev-h">{ic("calendar")}Upcoming events</h3>'
              f'<a href="{L(root, "announcements-events", "events")}">See all events {ic("arrow")}</a></div>'
              f'<div class="panel-body">{events_block(root, 3, True)}</div></section>'
              f'<section class="panel" aria-labelledby="an-h"><div class="panel-head green on-dark"><h3 id="an-h">{ic("bell")}Latest announcements</h3>'
              f'<a href="{L(root, "announcements-events", "announcements")}">See all {ic("arrow")}</a></div>'
              f'<div class="panel-body">{notices_block(root, 3)}</div></section>'
              f'</div></div></section>')

        cta = cta_band("Need help, or ready to get involved?",
                       "Talk to the Dean's Office, find a support service, or join campus life.",
                       ("Contact the Dean's Office", L(root, "contact-support")),
                       ("Explore Student Life", L(root, "student-life")))
        return h + s1 + s2 + s3 + cta

    page("index.html", "Karibu TUM | Student Affairs and Welfare Portal, Technical University of Mombasa",
         "Karibu TUM is the Student Affairs and Welfare Portal of Technical University of Mombasa: student life, support services, announcements and the Dean's Office.",
         "home", body)


def build_dean():
    def body(root):
        dn, msg_html = dean_about(root)
        svc = D["student_services"]
        biography = dn.get("biography") or [dn["summary"]]
        lead_html = f'<p>{e(biography[0])}</p>'
        biography_html = "".join(f'<p>{e(paragraph)}</p>' for paragraph in biography[1:])
        focus_areas = dn.get("focus_areas", [])
        focus_html = ""
        if focus_areas:
            focus_items = "".join(
                f'<li><strong>{e(item["title"])}:</strong> {e(item["description"])}</li>'
                for item in focus_areas
            )
            focus_html = (f'<div class="dean-focus-block"><h3>Leadership and Areas of Focus</h3>'
                          f'<ul class="dean-focus-list">{focus_items}</ul></div>')
        h = hero("Dean's Office",
                 "The Office of the Dean of Students looks after student welfare at Technical University of Mombasa and works with other departments so you can study, live and stay well on campus.",
                 root, tagline="Office of the Dean of Students",
                 actions=(f'<a class="btn btn-primary" href="#services">Explore our services {ic("arrow")}</a>'
                          f'<a class="btn btn-secondary" href="{L(root, "contact-support")}">Contact the office</a>'),
                 photo="assets/images/Bright Dean’s Office Waiting Hall.png",
                 photo_alt="Dean’s Office waiting hall",
                 crumbs=breadcrumbs(root, [("Home", L(root)), ("Dean's Office", "")]))

        reach = (f'<div class="side-panel dean-contact-panel"><h3>Reach the office</h3><p>Contact details for general enquiries.</p>'
                 f'<dl class="fact-list" style="margin-top:14px">'
                 f'{fact("mail", "Email", plain_mail(S["email_dean"]))}'
                 f'{fact("phone", "Phone", plain_tel())}'
                 f'{fact("pin", "Location", e(S["address"]) + "<br>" + e(S["po_box"]))}'
                 f'</dl></div>')
        s1 = (f'<section class="section dean-profile-section" id="about-dean" aria-labelledby="dean-h"><div class="container">'
              f'<div class="dean-profile-layout">{portrait(dn, root)}'
              f'<div class="dean-copy dean-profile-intro"><span class="gold-bar" aria-hidden="true"></span>'
              f'<h2 id="dean-h">About the Acting Dean</h2><p class="dean-name">{e(dn["name"])}</p>'
              f'<p class="dean-role">{e(dn["role"])}</p>{lead_html}</div></div>{reach}'
              f'<div class="dean-profile-details"><div class="dean-biography">{biography_html}</div>'
              f'{focus_html}</div>{msg_html}</div></section>')

        s2 = (f'<section class="section section-green" id="services" aria-labelledby="svc-h"><div class="container">'
              f'<div class="section-head centered"><div><span class="gold-bar" aria-hidden="true"></span>'
              f'<h2 id="svc-h">{e("Dean's Office services")}</h2><p>Access key services and support.</p></div></div>'
              f'<div class="grid grid-4">{"".join(service_card(s, root) for s in svc)}</div></div></section>')

        gallery_items = [
            {"src": "assets/images/Bright Dean’s Office Waiting Hall.png",
             "alt": "Bright waiting hall in the Dean’s Office",
             "caption": "Dean’s Office waiting hall"},
            {"src": "assets/images/Bright Clinic Corridor Waiting Area.png",
             "alt": "Bright clinic corridor waiting area",
             "caption": "Clinic corridor waiting area"},
        ]
        s_gallery = (f'<section class="section section-soft" id="gallery" aria-labelledby="gal-h"><div class="container">'
                     f'{section_head("Dean’s Office Gallery", "A look at student support spaces at TUM.")}'
                     f'{gallery(gallery_items, root, "the Dean’s Office")}</div></section>')

        staff = D["staff"]
        cards = "".join(staff_card(p, root) for p in staff)
        more = ""
        if len(staff) < 2:
            more = empty("users", "More team members to be added",
                         "Profiles for other staff in the Dean's Office will appear here once they are approved for publication.",
                         ("Contact the office", L(root, "contact-support")))
        staff_html = f'<div class="staff-layout"><div class="staff-cards">{cards}</div>{("<div class=" + chr(34) + "staff-more" + chr(34) + ">" + more + "</div>") if more else ""}</div>'
        s3 = (f'<section class="section" id="staff" aria-labelledby="staff-h"><div class="container">'
              f'<div class="section-head centered"><div><span class="gold-bar" aria-hidden="true"></span>'
              f'<h2 id="staff-h">Our Staff</h2><p>Meet the team at the Dean\'s Office.</p></div></div>'
              f'{staff_html}</div></section>')
        return h + s1 + s2 + s3 + s_gallery

    page("deans-office/index.html", "Dean's Office | Karibu TUM",
         "The Office of the Dean of Students at Technical University of Mombasa: the Dean, student services and the team.",
         "dean", body, lightbox=True)


def build_life():
    def body(root):
        life, svc = D["student_life"], D["student_services"]
        h = hero("Student Life",
                 "Join in, find your community and make time to play. Student life at TUM is about participation, recreation and belonging.",
                 root, actions=(f'<a class="btn btn-primary" href="#about-life">Explore opportunities {ic("arrow")}</a>'
                                f'<a class="btn btn-secondary" href="#student-services">Student services</a>'),
                 photo="assets/images/student-life/games 04.jpeg",
                 photo_alt="TUM students playing basketball on campus",
                 crumbs=breadcrumbs(root, [("Home", L(root)), ("Student Life", "")]))
        s1 = (f'<section class="section" id="about-life" aria-labelledby="about-h"><div class="container">'
              f'{section_head("About Student Life", "Clubs, sport and your students’ association: ways to take part beyond the classroom.")}'
              f'<div class="grid grid-3">{"".join(life_card(x, root) for x in life)}</div></div></section>')
        s2 = (f'<section class="section section-green" id="student-services" aria-labelledby="svc-h"><div class="container">'
              f'{section_head("Student Services", "Support for your health, wellbeing and accommodation, and help finding the right office.")}'
              f'<div class="grid grid-4">{"".join(service_card(s, root) for s in svc)}</div></div></section>')
        s1 = s1.replace('aria-labelledby="about-h"', 'aria-label="About Student Life"')
        s2 = s2.replace('aria-labelledby="svc-h"', 'aria-label="Student Services"')
        return h + s1 + s2

    page("student-life/index.html", "Student Life | Karibu TUM",
         "Clubs & Societies, Sports & Recreation, the Student Association and student services at Technical University of Mombasa.",
         "life", body)


def build_news():
    def body(root):
        h = hero("Announcements & Events",
                 "Notices from the Dean's Office, student events and the forms and documents you may need, all in one place.",
                 root, actions=(f'<a class="btn btn-primary" href="#events">See events {ic("arrow")}</a>'
                                f'<a class="btn btn-secondary" href="#announcements">Read announcements</a>'),
                 photo="assets/images/events.jpg",
                 photo_alt="Student presenting a project at a Technical University of Mombasa event",
                 crumbs=breadcrumbs(root, [("Home", L(root)), ("Announcements & Events", "")]))
        event_heading = ('<div class="event-feature-heading"><span>Upcoming &amp; Recent Events</span>'
                         '<h2>Featured Events</h2>'
                         '<p>Download official event letters for dates, venues, and full details.</p></div>')
        s1 = (f'<section class="section" id="events" aria-label="Events"><div class="container">'
              f'{event_heading}{event_cards_block(root)}</div></section>')
        s2 = (f'<section class="section section-soft" id="announcements" aria-label="Announcements"><div class="container">'
              f'{section_head("Announcements", "Notices and updates. Important notices carry an Important label.")}'
              f'<div class="panel"><div class="panel-body">{notices_block(root)}</div></div></div></section>')
        res = D["resources"]
        if res:
            rbody = f'<div class="panel"><div class="panel-body"><ul class="resource-list">{"".join(resource_row(r) for r in res)}</ul></div></div>'
        else:
            rbody = empty("file", "No downloads published yet",
                          "Forms, guides and other documents will be listed here when they are available. If you need a form now, email the Dean's Office.",
                          (S["email_dean"], "mailto:" + S["email_dean"]))
        s3 = (f'<section class="section" id="resources" aria-label="Resources download"><div class="container">'
              f'{section_head("Resources download", "Student forms, documents and guides.")}{rbody}</div></section>')
        return h + s1 + s2 + s3

    page("announcements-events/index.html", "Announcements & Events | Karibu TUM",
         "Announcements, upcoming events and downloadable student resources from the Dean's Office at Technical University of Mombasa.",
         "news", body)


def build_contact():
    def body(root):
        svc = D["student_services"]
        h = hero("Contact & Support",
                 "Reach the Dean's Office, ask a question or find the service that can help you.",
                 root, actions=(f'<a class="btn btn-primary" href="#enquiry">Send an enquiry {ic("send")}</a>'
                                f'<a class="btn btn-secondary" href="tel:{S["phone_tel"]}">Call {e(S["phone_display"])}</a>'),
                 crumbs=breadcrumbs(root, [("Home", L(root)), ("Contact & Support", "")]))
        cards = (f'<div class="contact-cards">'
                 f'<div class="contact-card"><span class="chip">{ic("mail")}</span><h3>Email</h3><p>Dean of Students</p><a href="mailto:{S["email_dean"]}">{e(S["email_dean"])}</a>'
                 f'<p>General university enquiries</p><a href="mailto:{S["email_general"]}">{e(S["email_general"])}</a></div>'
                 f'<div class="contact-card"><span class="chip">{ic("phone")}</span><h3>Phone</h3><p>University switchboard</p><a href="tel:{S["phone_tel"]}">{e(S["phone_display"])}</a></div>'
                 f'<div class="contact-card"><span class="chip">{ic("pin")}</span><h3>Visit</h3><p>{e(S["university"])}<br>{e(S["address"])}<br>{e(S["po_box"])}</p></div></div>')
        alert = (f'<div class="alert" role="note">{ic("alert")}<p><strong>In an emergency</strong>, call the Kenya emergency numbers '
                 f'<a href="tel:999">999</a> or <a href="tel:112">112</a>. This form is not monitored around the clock.</p></div>')
        s1 = (f'<section class="section" id="contact" aria-label="Contact details"><div class="container">'
              f'{section_head("Contact the Dean’s Office", "Use these details for general enquiries.")}{cards}{alert}</div></section>')
        s2 = (f'<section class="section section-green" id="find-support" aria-label="Find the right service"><div class="container">'
              f'{section_head("Find the right service", "Go straight to the service you need.")}'
              f'<div class="grid grid-4">{"".join(service_card(s, root) for s in svc)}</div></div></section>')
        opts = '<option value="">Choose one</option><option>Dean\'s Office (general)</option>' + "".join(
            f'<option>{e(s["title"])}</option>' for s in svc) + '<option>Student Life</option><option>Something else</option>'
        form = f'''<div class="form-card"><form id="enquiry-form" data-to="{S["email_dean"]}" novalidate>
<div class="form-grid">
<div class="field"><label for="f-name">Full name</label><input id="f-name" name="name" type="text" autocomplete="name" required aria-describedby="e-name"><span class="error" id="e-name" role="alert"></span></div>
<div class="field"><label for="f-reg">Registration number <span class="hint">(optional)</span></label><input id="f-reg" name="reg" type="text" autocomplete="off"></div>
<div class="field"><label for="f-email">Your email address</label><input id="f-email" name="email" type="email" autocomplete="email" required aria-describedby="e-email"><span class="error" id="e-email" role="alert"></span></div>
<div class="field"><label for="f-topic">Your enquiry is for</label><select id="f-topic" name="topic" required aria-describedby="e-topic">{opts}</select><span class="error" id="e-topic" role="alert"></span></div>
<div class="field full"><label for="f-msg">Message</label><textarea id="f-msg" name="message" required aria-describedby="e-msg"></textarea><span class="error" id="e-msg" role="alert"></span></div>
</div>
<p class="hint" style="margin:16px 0;color:var(--color-muted)">Sending opens your email app with this message addressed to {e(S["email_dean"])}. Please do not include sensitive personal details in a first message.</p>
<button class="btn btn-primary" type="submit">{ic("send")}Send enquiry</button>
<p class="form-status" id="form-status" role="status" aria-live="polite"></p>
</form></div>'''
        s3 = (f'<section class="section" id="enquiry" aria-label="Send an enquiry"><div class="container">'
              f'{section_head("Send an enquiry", "Tell us how we can help and we will point you to the right office.")}{form}</div></section>')
        return h + s1 + s2 + s3

    page("contact-support/index.html", "Contact & Support | Karibu TUM",
         "Contact the Dean's Office at Technical University of Mombasa, find a student service or send an enquiry.",
         "contact", body)


def build_service(s):
    def body(root):
        crumbs = breadcrumbs(root, [("Home", L(root)), ("Student Life", L(root, "student-life")),
                                    ("Student Services", L(root, "student-life", "student-services")), (s["title"], "")])
        h = hero(s["title"], s["hero_intro"], root,
                 actions=(f'<a class="btn btn-primary" href="{L(root, "contact-support")}">Contact &amp; Support</a>'
                          f'<a class="btn btn-secondary" href="#about">About this service</a>'),
                 photo=s["image"] if exists(s.get("image")) else None, crumbs=crumbs,
                 photo_alt=s.get("image_alt", ""))
        loc = e(s["location"]) if s.get("location") else pending(S["location_pending"])
        hrs = e(s["hours"]) if s.get("hours") else pending("Opening hours to be confirmed")
        if s.get("contact"):
            c = s["contact"]
            contact = ""
            if c.get("name"):
                contact += f'<strong>{e(c["name"])}</strong>'
            emails = list(c.get("emails", []))
            if c.get("email"):
                emails.append(c["email"])
            if emails:
                if contact:
                    contact += "<br>"
                contact += "<br>".join(plain_mail(email) for email in emails)
            if c.get("phone"):
                if contact:
                    contact += "<br>"
                contact += f'<a href="tel:{re.sub(r"[^+0-9]", "", c["phone"])}">{e(c["phone"])}</a>'
            for phone in c.get("phones", []):
                if contact:
                    contact += "<br>"
                contact += f'<a href="tel:{re.sub(r"[^+0-9]", "", phone)}">{e(phone)}</a>'
        else:
            contact = (f'{e("Dean's Office (general enquiries)")}<br>{plain_mail(S["email_dean"])}<br>{plain_tel()}')
        facts = (f'<aside class="facts" aria-label="Service details"><h3>At a glance</h3><dl class="fact-list">'
                 f'{fact("pin", "Location", loc)}{fact("clock", s.get("hours_label", "Opening hours"), hrs)}{fact("mail", "Contact", contact)}</dl></aside>')
        paras = "".join(f"<p>{e(p)}</p>" for p in s["about"])
        notice = (f'<div class="alert" role="note">{ic("alert")}<p><strong>Emergency:</strong> {e(s["emergency_notice"])}</p></div>'
                  if s.get("emergency_notice") else "")
        s1 = (f'<section class="section" id="about" aria-labelledby="about-h"><div class="container"><div class="detail-grid">'
              f'<div class="prose"><span class="gold-bar" aria-hidden="true"></span><h2 id="about-h">About the service</h2>{paras}'
              f'<div class="callout"><h3>How to access this service</h3><p>{e(s["access"])}</p></div>{notice}</div>{facts}</div></div></section>')
        accommodation_section = ""
        details = s.get("accommodation_details")
        if details:
            rate_items = "".join(
                f'<li><strong>{e(rate["category"])}</strong><span>{e(rate["rate"])}</span></li>'
                for rate in details.get("student_rates", [])
            )
            services = "".join(f"<li>{e(service)}</li>" for service in details.get("services", []))
            accommodation_section = (
                f'<section class="section section-soft" id="accommodation-details" aria-labelledby="accommodation-h"><div class="container">'
                f'<div class="section-head"><div><span class="gold-bar" aria-hidden="true"></span>'
                f'<h2 id="accommodation-h">Accommodation information</h2>'
                f'<p>Rates, support and services for students and visiting groups.</p></div></div>'
                f'<div class="accommodation-grid">'
                f'<article class="accommodation-card"><h3>Our vision</h3><p>{e(details["vision"])}</p>'
                f'<h3>Our mission</h3><p>{e(details["mission"])}</p></article>'
                f'<article class="accommodation-card"><h3>Student accommodation rates</h3><ul class="accommodation-rates">{rate_items}</ul>'
                f'<p class="accommodation-note">Rates cover accommodation only.</p>'
                f'<h3>Accommodation for visitors</h3><p>{e(details["visitor_rate"])} This rate covers accommodation only.</p></article>'
                f'<article class="accommodation-card"><h3>Services offered</h3><ul class="accommodation-services">{services}</ul></article>'
                f'<article class="accommodation-card accommodation-notice"><h3>Hostel notice</h3>'
                f'<p><strong>{e(details["cooking_notice"])}</strong></p><p>{e(details["cafeteria"])}</p></article>'
                f'</div></div></section>'
            )
        health_section = ""
        health = s.get("health_details")
        if health:
            eligibility = "".join(f"<li>{e(item)}</li>" for item in health["eligibility"])
            requirements = "".join(f"<li>{e(item)}</li>" for item in health["student_requirements"])
            clinical_services = "".join(f"<li>{e(item)}</li>" for item in health["services"])
            workflow = "".join(f"<li>{e(item)}</li>" for item in health["workflow"])
            insurance = "".join(f"<li>{e(item)}</li>" for item in health["insurance"])
            referrals = "".join(f"<li>{e(item)}</li>" for item in health["referral_hospitals"])
            emergency_tel = re.sub(r"[^+0-9]", "", health["after_hours_contact"])
            health_section = (
                f'<section class="section section-soft" id="health-centre-information" aria-labelledby="health-info-h"><div class="container">'
                f'<div class="section-head"><div><span class="gold-bar" aria-hidden="true"></span>'
                f'<h2 id="health-info-h">Health Centre information</h2>'
                f'<p>Care, eligibility and support available to the TUM community.</p></div></div>'
                f'<div class="health-grid">'
                f'<article class="health-card"><h3>Facility and eligibility</h3><p>{e(health["facility_level"])}</p>'
                f'<h4>Who can use the service</h4><ul>{eligibility}</ul>'
                f'<h4>What students should bring</h4><ul>{requirements}</ul></article>'
                f'<article class="health-card"><h3>Clinical services</h3><ul>{clinical_services}</ul></article>'
                f'<article class="health-card health-card-wide"><h3>Patient care pathway</h3><ol class="health-workflow">{workflow}</ol></article>'
                f'<article class="health-card"><h3>Accepted insurance partners</h3><ul>{insurance}</ul>'
                f'<h4>Referral hospitals</h4><ul>{referrals}</ul></article>'
                f'<article class="health-card health-card-notice"><h3>After-hours support</h3>'
                f'<p>After 5:00 PM, weekends and public holidays, call the In-Charge, Dr. Rerimoi, at '
                f'<a href="tel:{emergency_tel}">{e(health["after_hours_contact"])}</a>, or contact the TUM Security Officer on duty to reach the healthcare provider on call.</p>'
                f'<h4>Service limitation</h4><p>{e(health["service_limit"])}</p></article>'
                f'</div></div></section>'
            )
        wellbeing_section = ""
        wellbeing = s.get("wellbeing_details")
        if wellbeing:
            service_groups = ""
            for group in wellbeing["service_groups"]:
                services = "".join(f"<li>{e(service)}</li>" for service in group["services"])
                service_groups += (
                    f'<article class="wellbeing-card"><h3>{e(group["title"])}</h3>'
                    f'<ul>{services}</ul></article>'
                )
            care_approach = "".join(f"<li>{e(item)}</li>" for item in wellbeing["care_approach"])
            wellbeing_section = (
                f'<section class="section section-soft" id="wellbeing-information" aria-labelledby="wellbeing-h"><div class="container">'
                f'<div class="section-head"><div><span class="gold-bar" aria-hidden="true"></span>'
                f'<h2 id="wellbeing-h">Mental Health and Well-Being Centre</h2>'
                f'<p>{e(wellbeing["tagline"])}</p></div></div>'
                f'<div class="wellbeing-intro"><article class="wellbeing-card"><h3>Our vision</h3><p>{e(wellbeing["vision"])}</p>'
                f'<h3>Our mission</h3><p>{e(wellbeing["mission"])}</p></article>'
                f'<article class="wellbeing-card"><h3>Our approach</h3><ul>{care_approach}</ul>'
                f'<blockquote>{e(wellbeing["quote"])}</blockquote></article></div>'
                f'<div class="wellbeing-services">{service_groups}</div>'
                f'<div class="wellbeing-booking"><div><h3>Book a session</h3>'
                f'<p>Virtual and in-person appointments are available.</p></div>'
                f'<a class="btn btn-primary" href="{e(wellbeing["website"])}" target="_blank" rel="noopener">'
                f'Visit the Centre website {ic("external")}<span class="visually-hidden"> (opens in a new tab)</span></a></div>'
                f'</div></section>'
            )
        s2 = (f'<section class="section section-soft" id="gallery" aria-labelledby="gal-h"><div class="container">'
              f'<div class="section-head"><div><span class="gold-bar" aria-hidden="true"></span><h2 id="gal-h">Gallery</h2></div></div>'
              f'{gallery(s["gallery"], root, "this service")}</div></section>')
        subs = s.get("sub_services", [])
        if subs:
            sub_html = f'<div class="grid grid-3">{"".join(static_card(x["title"], x["description"], s["icon"]) for x in subs)}</div>'
        else:
            sub_html = empty("star", "Sub-services to be confirmed",
                             "Related support options for this service will be listed here once they are confirmed.",
                             ("Ask the Dean's Office", L(root, "contact-support", "enquiry")))
        s3 = (f'<section class="section" id="sub-services" aria-labelledby="sub-h"><div class="container">'
              f'<div class="section-head"><div><span class="gold-bar" aria-hidden="true"></span><h2 id="sub-h">Sub-services</h2>'
              f'<p>Related support options within {e(s["title"])}.</p></div></div>{sub_html}</div></section>')
        return h + s1 + accommodation_section + health_section + wellbeing_section + s2 + s3

    page(f"student-services/{s['slug']}/index.html", f"{s['title']} | Karibu TUM",
         s["short"], "life", body, lightbox=bool(s["gallery"]))


def build_life_detail(t):
    def body(root):
        crumbs = breadcrumbs(root, [("Home", L(root)), ("Student Life", L(root, "student-life")), (t["title"], "")])
        secondary_action = (
            '<a class="btn btn-secondary" href="https://www.tumsocial.co.ke/politics" target="_blank" rel="noopener">'
            'TUMSA Elections<span class="visually-hidden"> (opens in a new tab)</span></a>'
            if t["slug"] == "student-association"
            else '<a class="btn btn-secondary" href="#about">About this area</a>'
        )
        h = hero(t["title"], t["hero_intro"], root,
                 actions=(f'<a class="btn btn-primary" href="{L(root, "contact-support")}">Ask the Dean’s Office</a>'
                          f'{secondary_action}'),
                 photo=t["image"] if exists(t.get("image")) else None, crumbs=crumbs,
                 photo_alt=t.get("image_alt", ""))
        clubs_details = t.get("clubs_details")
        if clubs_details:
            venue_items = "".join(
                f'<div><dt>{e(item["name"])}</dt><dd>{e(item.get("venue") or "Venue to be confirmed")}</dd></div>'
                for section in clubs_details["sections"]
                for item in section["items"]
            )
            facts = (f'<aside class="facts" aria-label="Club venues"><h3>Club venues</h3>'
                     f'<dl class="fact-list club-venue-list">{venue_items}</dl></aside>')
        else:
            loc = e(t["location"]) if t.get("location") else pending(S["location_pending"])
            facts = (f'<aside class="facts" aria-label="Details"><h3>At a glance</h3><dl class="fact-list">'
                     f'{fact("pin", "Location or venue", loc)}'
                     f'{fact("mail", "Contact", e("Dean's Office (general enquiries)") + "<br>" + plain_mail(S["email_dean"]) + "<br>" + plain_tel())}'
                     f'</dl></aside>')
        why_join = ""
        if clubs_details and clubs_details.get("why_join"):
            benefits = "".join(f"<li>{e(benefit)}</li>" for benefit in clubs_details["why_join"])
            why_join = (f'<div class="callout club-benefits"><h3>Why get involved?</h3>'
                        f'<ul>{benefits}</ul></div>')
        paras = "".join(f"<p>{e(p)}</p>" for p in t["about"])
        s1 = (f'<section class="section" id="about" aria-labelledby="about-h"><div class="container"><div class="detail-grid">'
              f'<div class="prose"><span class="gold-bar" aria-hidden="true"></span><h2 id="about-h">About {e(t["title"])}</h2>{paras}'
              f'<div class="callout"><h3>How to take part</h3><p>{e(t["participate"])}</p></div>{why_join}</div>{facts}</div></div></section>')
        clubs = ""
        if clubs_details:
            club_cards = []
            for section in clubs_details["sections"]:
                items = "".join(
                    f'<li><strong>{e(item["name"])}</strong> {e(item["description"])}</li>'
                    for item in section["items"]
                )
                club_cards.append(
                    f'<article class="association-card"><h3>{e(section["title"])}</h3><ul>{items}</ul></article>'
                )
            clubs = (
                f'<section class="section section-soft" id="clubs" aria-labelledby="clubs-h"><div class="container">'
                f'<div class="section-head"><div><span class="gold-bar" aria-hidden="true"></span>'
                f'<h2 id="clubs-h">Prominent Clubs and Societies at TUM</h2></div></div>'
                f'<div class="grid grid-2 association-grid">{"".join(club_cards)}</div></div></section>'
            )
        association = ""
        association_details = t.get("association_details")
        if association_details:
            association_cards = []
            for section in association_details["sections"]:
                paragraphs = "".join(f"<p>{e(paragraph)}</p>" for paragraph in section["paragraphs"])
                points = "".join(f"<li>{e(point)}</li>" for point in section["points"])
                point_list = f"<ul>{points}</ul>" if points else ""
                association_cards.append(
                    f'<article class="association-card"><h3>{e(section["title"])}</h3>'
                    f'{paragraphs}{point_list}</article>'
                )
            association = (
                f'<section class="section section-soft" id="representation" aria-labelledby="representation-h">'
                f'<div class="container"><div class="section-head"><div><span class="gold-bar" aria-hidden="true"></span>'
                f'<h2 id="representation-h">Representation, welfare and participation</h2>'
                f'<p>Key roles and responsibilities described in the TUMSA Constitution.</p></div></div>'
                f'<div class="grid grid-2 association-grid">{"".join(association_cards)}</div>'
                f'<div class="association-commitment"><strong>Your voice matters.</strong> '
                f'{e(association_details["commitment"])}</div></div></section>'
            )
        sports_section = ""
        sports = t.get("sports_details")
        if sports:
            rows = "".join(
                f'<tr><th scope="row">{e(event["date"])}</th><td>{e(event["activity"])}</td>'
                f'<td>{e(event["event"])}</td><td>{e(event["venue"])}</td></tr>'
                for event in sports["calendar"]
            )
            proposed_changes = "".join(f"<li>{e(change)}</li>" for change in sports.get("proposed_changes", []))
            students = ", ".join(e(name) for name in sports["world_cup"]["students"])
            sports_section = (
                f'<section class="section section-soft" id="sports-calendar" aria-labelledby="sports-calendar-h"><div class="container">'
                f'<div class="section-head"><div><span class="gold-bar" aria-hidden="true"></span>'
                f'<h2 id="sports-calendar-h">KUSF Coast Conference Calendar {e(sports["season"])}</h2>'
                f'<p>{e(sports["source_note"])}</p></div></div>'
                f'<div class="sports-table-wrap"><table class="sports-calendar"><thead><tr>'
                f'<th scope="col">Date</th><th scope="col">Sports &amp; activities</th>'
                f'<th scope="col">Event</th><th scope="col">Host / venue</th>'
                f'</tr></thead><tbody>{rows}</tbody></table></div>'
                f'<aside class="sports-proposals"><h3>Proposed calendar changes</h3><ul>{proposed_changes}</ul>'
                f'<p>These are listed as proposals in the source document, not as confirmed changes to the approved calendar.</p></aside>'
                f'<article class="sports-feature"><div><span class="gold-bar" aria-hidden="true"></span>'
                f'<h3>TUM at the Woodball World Cup</h3>'
                f'<p>{e(students)} are attending the {e(sports["world_cup"]["event"])} in {e(sports["world_cup"]["location"])}.</p></div>'
                f'<a class="btn btn-primary" href="mailto:{e(sports["world_cup"]["contact"])}">Contact the Sports Officer</a></article>'
                f'</div></section>'
            )
        s2 = (f'<section class="section section-soft" id="gallery" aria-labelledby="gal-h"><div class="container">'
              f'<div class="section-head"><div><span class="gold-bar" aria-hidden="true"></span><h2 id="gal-h">Gallery</h2></div></div>'
              f'{gallery(t["gallery"], root, t["title"])}</div></section>')
        related = [x for x in D["student_life"] if x["slug"] != t["slug"]]
        if related:
            rel_html = f'<div class="grid grid-3">{"".join(life_card(x, root) for x in related)}</div>'
        else:
            rel_html = empty("users", "No related topics yet", "More Student Life topics will appear here.")
        s3 = (f'<section class="section" id="related" aria-labelledby="rel-h"><div class="container">'
              f'<div class="section-head"><div><span class="gold-bar" aria-hidden="true"></span><h2 id="rel-h">Related Student Life</h2>'
              f'<p>More ways to get involved.</p></div>'
              f'<a class="btn btn-soft" href="{L(root, "student-life")}">All of Student Life {ic("arrow")}</a></div>{rel_html}</div></section>')
        return h + s1 + clubs + association + sports_section + s2 + s3

    page(f"student-life/{t['slug']}/index.html", f"{t['title']} | Student Life | Karibu TUM",
         t["short"], "life", body, lightbox=bool(t["gallery"]))


def build_404():
    def body(root):
        return (f'<section class="notfound"><div class="container"><span class="gold-bar" style="margin-inline:auto" aria-hidden="true"></span>'
                f'<h1>We can’t find that page</h1><p>The link may be out of date. Try the homepage or contact the Dean’s Office.</p>'
                f'<div class="btn-row" style="justify-content:center"><a class="btn btn-primary" href="{L(root)}">Go to the homepage</a>'
                f'<a class="btn btn-secondary" href="{L(root, "contact-support")}">Contact &amp; Support</a></div></div></section>')
    page("404.html", "Page not found | Karibu TUM", "Page not found.", "", body)


if __name__ == "__main__":
    build_home()
    build_dean()
    build_life()
    build_news()
    build_contact()
    for s in D["student_services"]:
        build_service(s)
    for t in D["student_life"]:
        build_life_detail(t)
    build_404()
    print("done")
