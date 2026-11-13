# Karibu TUM: asset map and content to-do

## What Image-assets.zip contained
- `References/Homepage.png` and `References/Dean’s Office Mockup.png`: AI-style design mockups. Used only as layout guidance. **Not placed in the site.** They show invented staff names (Dr. Jane Doe etc.), events and announcements that are not verified.
- `images/`: empty. No official logo, Dean portrait, staff portraits or campus/student photos were supplied.

## Image slots (drop file in, set path in data/content.json, run `python3 build.py`)
| Where | Folder / JSON field |
|---|---|
| Official TUM logo | `assets/images/TUM logo.png` (used in the shared header on every page) |
| Homepage hero photo | `assets/images/hero/campus.jpg` (auto-detected) |
| Dean's Office / Student Life / Events hero | `assets/images/hero/deans-office.jpg`, `student-life.jpg`, `events.jpg` |
| Dean portrait | `dean.portrait` + `dean.portrait_alt` |
| Staff portraits | `staff[].portrait` + `portrait_alt` |
| Student Life cards and detail heroes | `student_life[].image` + `image_alt` |
| Service detail heroes | `student_services[].image` + `image_alt` |
| Galleries | `gallery: [{"src": "...", "alt": "...", "caption": "..."}]` |

## Content still needed from the site owner (shown as "to be confirmed" or empty states)
- Dean's message (approved text); Dean portrait; other staff names, titles, approved contacts.
- Location, opening hours and contact details for each service and Student Life topic.
- How to join clubs, sports, TUMSA; schedules and eligibility.
- Events, announcements, downloadable resources (arrays are empty; templates render them when filled).
- Customer Care description is generic wording; confirm it.
- Sub-services for Guidance & Counselling, Health Unit, Customer Care.

## Footer
The shared footer in `build.py` follows `screenshots/footer.jpg` and is generated onto every page, including `404.html`. The screenshot provides the contact numbers and the displayed footer groups. Outbound links whose exact destinations are not shown currently point to the official TUM homepage; replace those with verified deep links when available. Social badges are visual only until official profile URLs are confirmed, and “Cookies settings” is a display label because this site does not currently have a cookie-consent interface.

## Verified source for facts used
Contact details and section structure: design.md. Dean's name and role, and the Dean's Office remit: TUM Student Handbook and Dean's welcome message on web.tum.ac.ke. Hostel/off-campus wording: web.tum.ac.ke campus-life page.
