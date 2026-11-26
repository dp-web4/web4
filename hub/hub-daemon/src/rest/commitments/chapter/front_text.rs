//! Reading the page maintainer's free-text event fields well enough to draw them.
//!
//! An event's `when`, `where` and `note` are plain text (`hub_lib::chapter_page::PageEvent`). The
//! front page draws a date stamp, a Portland quadrant chip and a turnout bar only when the text
//! reads unambiguously; anything it can't read is shown as the maintainer wrote it. So these
//! parsers are strict: one word they don't recognise and they give up.

use chrono::{Datelike, Duration, NaiveDate, NaiveTime, Weekday};

/// A `when` that reads as one date, with an optional start and end time.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct When {
    pub date: NaiveDate,
    pub start: Option<NaiveTime>,
    pub end: Option<NaiveTime>,
}

/// Which way to look for the year when the text doesn't give one.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum Toward {
    /// The next such date (a little slack for an event that was yesterday).
    Ahead,
    /// The last such date (a little slack for one that's tomorrow).
    Behind,
}

const SLACK_DAYS: i64 = 7;

fn weekday_of(w: &str) -> Option<Weekday> {
    Some(match w {
        "mon" | "monday" => Weekday::Mon,
        "tue" | "tues" | "tuesday" => Weekday::Tue,
        "wed" | "weds" | "wednesday" => Weekday::Wed,
        "thu" | "thur" | "thurs" | "thursday" => Weekday::Thu,
        "fri" | "friday" => Weekday::Fri,
        "sat" | "saturday" => Weekday::Sat,
        "sun" | "sunday" => Weekday::Sun,
        _ => return None,
    })
}

fn month_of(w: &str) -> Option<u32> {
    Some(match w {
        "jan" | "january" => 1,
        "feb" | "february" => 2,
        "mar" | "march" => 3,
        "apr" | "april" => 4,
        "may" => 5,
        "jun" | "june" => 6,
        "jul" | "july" => 7,
        "aug" | "august" => 8,
        "sep" | "sept" | "september" => 9,
        "oct" | "october" => 10,
        "nov" | "november" => 11,
        "dec" | "december" => 12,
        _ => return None,
    })
}

/// "7", "7th", "21st": a day of the month.
fn day_of(w: &str) -> Option<u32> {
    let digits = w.trim_end_matches(|c: char| c.is_ascii_alphabetic());
    let suffix = &w[digits.len()..];
    if digits.is_empty() || digits.len() > 2 || !digits.chars().all(|c| c.is_ascii_digit()) {
        return None;
    }
    if !matches!(suffix, "" | "st" | "nd" | "rd" | "th") {
        return None;
    }
    digits.parse().ok().filter(|d| (1..=31).contains(d))
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Mer { Am, Pm }

/// One clock reading: "6", "6pm", "6:30", "6:30pm", "18:00".
#[derive(Clone, Copy, Debug)]
struct Clock { h: u32, m: u32, colon: bool, mer: Option<Mer> }

fn mer_of(w: &str) -> Option<Mer> {
    match w {
        "am" | "a.m." | "a.m" => Some(Mer::Am),
        "pm" | "p.m." | "p.m" => Some(Mer::Pm),
        _ => None,
    }
}

fn clock_of(w: &str) -> Option<Clock> {
    let (num, mer) = ["a.m.", "p.m.", "a.m", "p.m", "am", "pm"].iter()
        .find_map(|s| w.strip_suffix(s).map(|n| (n, mer_of(s))))
        .unwrap_or((w, None));
    let (h, m, colon) = match num.split_once(':') {
        Some((h, m)) if m.len() == 2 => (h, m, true),
        Some(_) => return None,
        None => (num, "0", false),
    };
    if h.is_empty() || h.len() > 2 || !h.chars().all(|c| c.is_ascii_digit()) || !m.chars().all(|c| c.is_ascii_digit()) {
        return None;
    }
    let (h, m): (u32, u32) = (h.parse().ok()?, m.parse().ok()?);
    if m > 59 || h > 23 || (mer.is_some() && !(1..=12).contains(&h)) {
        return None;
    }
    Some(Clock { h, m, colon, mer })
}

impl Clock {
    /// The time, if it's unambiguous: it says am/pm, or it's a 24-hour reading ("18:00", "09:30").
    fn time(self, mer: Option<Mer>) -> Option<NaiveTime> {
        let h = match self.mer.or(mer) {
            Some(Mer::Am) => self.h % 12,
            Some(Mer::Pm) => self.h % 12 + 12,
            None if self.colon && (self.h >= 13 || self.h == 0) => self.h,
            None => return None,
        };
        NaiveTime::from_hms_opt(h, self.m, 0)
    }
}

/// Read a `when`: "Thu Dec 10, 6pm", "Thursday, Dec 10 · 6–9 pm", "December 10 2026 at 18:00",
/// "2026-12-10", "Sat Nov 7". A weekday, if given, must match the date. `None` if any part of
/// the text isn't a date or a time.
pub(crate) fn parse_when(text: &str, today: NaiveDate, toward: Toward) -> Option<When> {
    let lower = text.trim().to_lowercase();
    if lower.is_empty() || lower.len() > 80 {
        return None;
    }
    // Separators become spaces; a dash between two numbers is a range.
    let mut s = String::with_capacity(lower.len());
    for c in lower.chars() {
        match c {
            ',' | '·' | '|' | '@' | '(' | ')' | '•' => s.push(' '),
            '–' | '—' => s.push_str(" - "),
            _ => s.push(c),
        }
    }
    let (mut wd, mut month, mut day, mut year, mut iso) = (None, None, None, None, None);
    let mut clocks: Vec<Clock> = Vec::new();
    let mut trailing_mer: Option<Mer> = None;
    for raw in s.split_whitespace() {
        let w = raw.trim_end_matches('.');
        if let Ok(d) = NaiveDate::parse_from_str(raw, "%Y-%m-%d") {
            if iso.replace(d).is_some() { return None; }
            continue;
        }
        if matches!(w, "at" | "from" | "to" | "until" | "till" | "-" | "on") {
            continue;
        }
        if let Some(d) = weekday_of(w) {
            if wd.replace(d).is_some() { return None; }
            continue;
        }
        if let Some(m) = month_of(w) {
            if month.replace(m).is_some() { return None; }
            continue;
        }
        if let Some(m) = mer_of(raw) {
            trailing_mer = Some(m);
            for c in clocks.iter_mut().filter(|c| c.mer.is_none()) { c.mer = Some(m); }
            continue;
        }
        if w.len() == 4 && w.chars().all(|c| c.is_ascii_digit()) {
            let y: i32 = w.parse().ok()?;
            if !(2000..=2100).contains(&y) || year.replace(y).is_some() { return None; }
            continue;
        }
        // "6-9pm" in one word: a range of clocks.
        let pieces: Vec<&str> = raw.split('-').filter(|p| !p.is_empty()).collect();
        if pieces.len() == 1 && day.is_none() && clocks.is_empty() {
            if let Some(d) = day_of(w) {
                day = Some(d);
                continue;
            }
        }
        if pieces.is_empty() || pieces.len() > 2 {
            return None;
        }
        for p in pieces {
            clocks.push(clock_of(p)?);
        }
        if clocks.len() > 2 { return None; }
    }
    let _ = trailing_mer;
    let date = match (iso, month, day) {
        (Some(d), None, None) if year.is_none() => d,
        (None, Some(m), Some(d)) => match year {
            Some(y) => NaiveDate::from_ymd_opt(y, m, d)?,
            None => {
                let candidates = (today.year() - 1..=today.year() + 1)
                    .filter_map(|y| NaiveDate::from_ymd_opt(y, m, d))
                    .filter(|c| wd.map_or(true, |w| c.weekday() == w));
                match toward {
                    Toward::Ahead => candidates.filter(|c| *c >= today - Duration::days(SLACK_DAYS)).min()?,
                    Toward::Behind => candidates.filter(|c| *c <= today + Duration::days(SLACK_DAYS)).max()?,
                }
            }
        },
        _ => return None,
    };
    if wd.is_some_and(|w| date.weekday() != w) {
        return None;
    }
    // "6-9 pm": the end's am/pm carries back to the start when the start has none.
    let (start, end) = match clocks.as_slice() {
        [] => (None, None),
        [a] => (Some(a.time(None)?), None),
        [a, b] => {
            let e = b.time(None)?;
            let s = a.time(b.mer).or_else(|| a.time(None))?;
            (Some(s), Some(e))
        }
        _ => return None,
    };
    Some(When { date, start, end })
}

fn clock_words(t: NaiveTime, with_mer: bool) -> String {
    let (pm, h) = t.hour12();
    let mut s = if t.minute() == 0 { h.to_string() } else { format!("{h}:{:02}", t.minute()) };
    if with_mer {
        s.push_str(if pm { " pm" } else { " am" });
    }
    s
}
use chrono::Timelike;

impl When {
    /// "Thursday, Dec 10", with the year when it isn't this year's.
    pub fn day_words(&self, today: NaiveDate) -> String {
        if self.date.year() == today.year() {
            self.date.format("%A, %b %-d").to_string()
        } else {
            self.date.format("%A, %b %-d, %Y").to_string()
        }
    }

    /// "Sat Nov 7", short, for a list.
    pub fn short_day(&self) -> String {
        self.date.format("%a %b %-d").to_string()
    }

    /// "6–9 pm", "11 am–1 pm", "6:30 pm", or empty.
    pub fn time_words(&self) -> String {
        match (self.start, self.end) {
            (Some(s), Some(e)) => {
                let same = s.hour12().0 == e.hour12().0;
                format!("{}–{}", clock_words(s, !same), clock_words(e, true))
            }
            (Some(s), None) => clock_words(s, true),
            _ => String::new(),
        }
    }

    /// For `<time datetime>`: "2026-12-10T18:00" or "2026-12-10".
    pub fn machine(&self) -> String {
        match self.start {
            Some(t) => format!("{}T{}", self.date.format("%Y-%m-%d"), t.format("%H:%M")),
            None => self.date.format("%Y-%m-%d").to_string(),
        }
    }

    /// Month, day and weekday for the date stamp: ("DEC", "10", "THU").
    pub fn stamp(&self) -> (String, String, String) {
        (self.date.format("%b").to_string().to_uppercase(), self.date.day().to_string(),
            self.date.format("%a").to_string().to_uppercase())
    }
}

/// Portland's address quadrants.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum Quad { N, NE, NW, SE, SW, S }

impl Quad {
    pub fn code(self) -> &'static str {
        match self { Quad::N => "N", Quad::NE => "NE", Quad::NW => "NW", Quad::SE => "SE", Quad::SW => "SW", Quad::S => "S" }
    }
    pub fn name(self) -> &'static str {
        match self {
            Quad::N => "North", Quad::NE => "Northeast", Quad::NW => "Northwest",
            Quad::SE => "Southeast", Quad::SW => "Southwest", Quad::S => "South",
        }
    }
}

fn quad_code(w: &str) -> Option<Quad> {
    match w.replace('.', "").as_str() {
        "N" => Some(Quad::N), "NE" => Some(Quad::NE), "NW" => Some(Quad::NW),
        "SE" => Some(Quad::SE), "SW" => Some(Quad::SW), "S" => Some(Quad::S),
        _ => None,
    }
}

fn quad_word(w: &str) -> Option<Quad> {
    match w.to_lowercase().as_str() {
        "north" => Some(Quad::N), "northeast" => Some(Quad::NE), "northwest" => Some(Quad::NW),
        "southeast" => Some(Quad::SE), "southwest" => Some(Quad::SW), "south" => Some(Quad::S),
        _ => None,
    }
}

/// A `where` with a quadrant in it.
#[derive(Clone, Debug, PartialEq, Eq)]
pub(crate) struct Where {
    pub quad: Quad,
    /// The main line: the place, without a leading quadrant word.
    pub place: String,
    /// What came after the first " · " or ", " (a venue note), if anything.
    pub detail: String,
}

/// Find the quadrant in a `where`: a leading "SE", "S.E.", "Southeast" (optionally followed by
/// "Portland"), or a two-letter code ("NE", "SW"…) as a word anywhere ("1050 SE Water Ave"). A
/// lone "N" or "S" counts only at the start, followed by a capitalised word ("N Williams Ave").
pub(crate) fn parse_where(text: &str) -> Option<Where> {
    let t = text.trim();
    if t.is_empty() {
        return None;
    }
    let (head, rest) = match t.find([',', '·']) {
        Some(i) => (t[..i].trim(), t[i..].trim_start_matches([',', '·']).trim()),
        None => (t, ""),
    };
    let words: Vec<&str> = head.split_whitespace().collect();
    let first = words.first().copied().unwrap_or_default();
    let next_is_name = words.get(1).is_some_and(|w| w.chars().next().is_some_and(|c| c.is_uppercase() || c.is_ascii_digit()));
    let lead = match (quad_code(first), quad_word(first)) {
        (Some(q @ (Quad::N | Quad::S)), _) if next_is_name => Some(q),
        (Some(q), _) if !matches!(q, Quad::N | Quad::S) => Some(q),
        (_, Some(q)) => Some(q),
        _ => None,
    };
    if let Some(q) = lead {
        let mut place = words[1..].join(" ");
        if place.eq_ignore_ascii_case("portland") || place.is_empty() {
            place = format!("{} Portland", q.name());
        }
        return Some(Where { quad: q, place, detail: rest.to_string() });
    }
    // A two-letter code anywhere in the whole text: keep the text as written.
    let q = t.split(|c: char| c.is_whitespace() || c == ',' || c == '·')
        .find_map(|w| quad_code(w).filter(|q| !matches!(q, Quad::N | Quad::S)).filter(|_| w.len() >= 2))?;
    Some(Where { quad: q, place: head.to_string(), detail: rest.to_string() })
}

/// The turnout in a note: "70+ signed up", "about 1,200 people came", "45 RSVPs". `None`
/// unless a number sits right before a word about people.
pub(crate) fn parse_turnout(note: &str) -> Option<u32> {
    const PEOPLE: &[&str] = &["signed", "signups", "sign-ups", "came", "people", "attendees", "attended", "rsvps",
        "rsvp'd", "rsvpd", "showed", "builders", "guests", "joined", "registered", "folks", "hackers", "members"];
    let words: Vec<String> = note.split_whitespace()
        .map(|w| w.trim_matches(|c: char| !c.is_alphanumeric() && c != '+' && c != '\'' && c != '-').to_lowercase())
        .collect();
    for (i, w) in words.iter().enumerate() {
        let n = w.trim_end_matches('+').replace(',', "");
        if n.is_empty() || !n.chars().all(|c| c.is_ascii_digit()) || n.len() > 6 {
            continue;
        }
        let near = words.iter().skip(i + 1).take(2);
        if near.clone().any(|x| PEOPLE.iter().any(|p| x == p || x.starts_with(p))) {
            return n.parse().ok().filter(|n| *n > 0);
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;

    fn d(y: i32, m: u32, dd: u32) -> NaiveDate { NaiveDate::from_ymd_opt(y, m, dd).unwrap() }
    fn t(h: u32, m: u32) -> NaiveTime { NaiveTime::from_hms_opt(h, m, 0).unwrap() }
    const TODAY: fn() -> NaiveDate = || d(2026, 11, 25);

    #[test]
    fn whens_that_read() {
        let a = parse_when("Thu Dec 10, 6pm", TODAY(), Toward::Ahead).unwrap();
        assert_eq!((a.date, a.start, a.end), (d(2026, 12, 10), Some(t(18, 0)), None));
        let b = parse_when("Thursday, Dec 10 · 6–9 pm", TODAY(), Toward::Ahead).unwrap();
        assert_eq!((b.start, b.end), (Some(t(18, 0)), Some(t(21, 0))));
        assert_eq!(b.time_words(), "6–9 pm");
        assert_eq!(b.machine(), "2026-12-10T18:00");
        assert_eq!(b.day_words(TODAY()), "Thursday, Dec 10");
        assert_eq!(b.stamp(), ("DEC".into(), "10".into(), "THU".into()));
        let c = parse_when("Jan 14 at 11am-1pm", TODAY(), Toward::Ahead).unwrap();
        assert_eq!(c.date, d(2027, 1, 14));
        assert_eq!(c.time_words(), "11 am–1 pm");
        assert_eq!(c.day_words(TODAY()), "Thursday, Jan 14, 2027");
        assert_eq!(parse_when("2026-12-10 18:30", TODAY(), Toward::Ahead).unwrap().machine(), "2026-12-10T18:30");
        assert_eq!(parse_when("December 10th 2026", TODAY(), Toward::Ahead).unwrap().machine(), "2026-12-10");
        // A recent event: the last Nov 7, a Saturday.
        let r = parse_when("Sat Nov 7", TODAY(), Toward::Behind).unwrap();
        assert_eq!((r.date, r.short_day()), (d(2026, 11, 7), "Sat Nov 7".to_string()));
        // Last July, looking back; next July, looking ahead.
        assert_eq!(parse_when("Jul 15", TODAY(), Toward::Behind).unwrap().date, d(2026, 7, 15));
        assert_eq!(parse_when("Jul 15", TODAY(), Toward::Ahead).unwrap().date, d(2027, 7, 15));
    }

    #[test]
    fn whens_that_dont() {
        for s in ["Second Thursday in December, doors 6-ish", "TBA", "", "Dec", "Dec 10, 6", "Dec 10 6:00",
            "Mon Dec 10" /* Dec 10 is a Wed, Thu, Fri in 2025–27 */, "Dec 32", "soon-ish"] {
            assert!(parse_when(s, TODAY(), Toward::Ahead).is_none(), "{s}");
        }
    }

    #[test]
    fn wheres() {
        let w = parse_where("SE Central Eastside · Venue on RSVP").unwrap();
        assert_eq!((w.quad, w.place.as_str(), w.detail.as_str()), (Quad::SE, "Central Eastside", "Venue on RSVP"));
        assert_eq!(parse_where("Southeast Portland").unwrap().place, "Southeast Portland");
        assert_eq!(parse_where("S.E. Division St").unwrap().quad, Quad::SE);
        let a = parse_where("1050 SE Water Ave, 2nd floor").unwrap();
        assert_eq!((a.quad, a.place.as_str(), a.detail.as_str()), (Quad::SE, "1050 SE Water Ave", "2nd floor"));
        assert_eq!(parse_where("N Williams Ave").unwrap().quad, Quad::N);
        assert_eq!(parse_where("Northwest, Pearl District").unwrap().place, "Northwest Portland");
        for s in ["Downtown Portland", "Inner eastside, address on Luma", "S of the river", "", "Nowhere"] {
            assert!(parse_where(s).is_none(), "{s}");
        }
    }

    #[test]
    fn turnouts() {
        assert_eq!(parse_turnout("70+ signed up for a day of building together."), Some(70));
        assert_eq!(parse_turnout("About 1,200 people came"), Some(1200));
        assert_eq!(parse_turnout("45 RSVPs"), Some(45));
        assert_eq!(parse_turnout("About seventy, standing room by 7"), None);
        assert_eq!(parse_turnout("Round 2 of the series"), None);
        assert_eq!(parse_turnout(""), None);
    }
}
