// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! The chapter's front page (`hub/docs/PRD_CHAPTER_FRONT_PAGE.md`).
//!
//! The page is **structured content, never markup**. Whoever fills it, usually a co-lead's AI
//! assistant acting as the chapter's *page maintainer*, supplies text and links, and the hub
//! renders them escaped. That keeps the public page script-free, whatever an assistant is told
//! to write.
//!
//! Two parts are kept, both content-addressed:
//! - **page**: what the public front page says ([`PageContent`]);
//! - **brief**: the page maintainer's context (voice, audience, rules, chapter facts), owned by
//!   the co-leads. The default is `examples/chapter/page-maintainer/brief.md`.
//!
//! Only a part's digest reaches the ledger (`chapter_page_set`, `chapter_page_proposed`). The
//! text lives in the operator's page file, so the record says who changed what and when, and the
//! words stay off the ledger. The file is checked against the ledger's digest on every read.

use serde::{Deserialize, Serialize};

pub const MAX_HEADLINE: usize = 90;
pub const MAX_STORY: usize = 600;
pub const MAX_TITLE: usize = 90;
pub const MAX_WHEN: usize = 40;
pub const MAX_WHERE: usize = 80;
pub const MAX_NOTE: usize = 160;
pub const MAX_WAY_TITLE: usize = 50;
pub const MAX_WAY_TEXT: usize = 200;
pub const MAX_CONTACT: usize = 120;
pub const MAX_LABEL: usize = 40;
pub const MAX_URL: usize = 300;
pub const MAX_EVENTS: usize = 3;
pub const MAX_WAYS: usize = 4;
pub const MAX_LINKS: usize = 5;
pub const MAX_BRIEF: usize = 8000;

/// The only role that keeps the page today. A role, not a person: its law is the hub law's
/// norms on `r6.role == page_maintainer`, its context is the brief.
pub const PAGE_MAINTAINER: &str = "page_maintainer";

/// The default brief, with `{chapter}` for the chapter's name.
pub const DEFAULT_BRIEF: &str = include_str!("../../examples/chapter/page-maintainer/brief.md");

/// What the public front page says. Every field is plain text or an https link.
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PageContent {
    /// Why people come, in the chapter's voice. One line.
    pub headline: String,
    /// Two or three sentences. Blank lines separate paragraphs.
    #[serde(default)]
    pub story: String,
    /// The next events.
    #[serde(default)]
    pub next: Vec<PageEvent>,
    /// Recent events, each with a line of proof.
    #[serde(default)]
    pub recent: Vec<PageEvent>,
    /// Ways to take part.
    #[serde(default)]
    pub ways_in: Vec<PageWay>,
    /// An email address or an https link. Empty shows a placeholder.
    #[serde(default)]
    pub contact: String,
    #[serde(default)]
    pub links: Vec<PageLink>,
    /// List the chapter's committees (names and purposes, never people).
    #[serde(default = "yes")]
    pub show_committees: bool,
}

fn yes() -> bool {
    true
}

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PageEvent {
    pub title: String,
    #[serde(default)]
    pub when: String,
    #[serde(default, rename = "where")]
    pub place: String,
    #[serde(default)]
    pub note: String,
    #[serde(default)]
    pub link: String,
}

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PageWay {
    pub title: String,
    #[serde(default)]
    pub text: String,
    #[serde(default)]
    pub link: String,
}

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PageLink {
    pub label: String,
    pub url: String,
}

/// Which part of the front page an act sets.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PagePart {
    Page,
    Brief,
}

impl PagePart {
    pub fn as_str(self) -> &'static str {
        match self {
            PagePart::Page => "page",
            PagePart::Brief => "brief",
        }
    }
}

/// How a front-page act reached the hub.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PageVia {
    /// A co-lead, from their own chapter page.
    Link,
    /// A page maintainer (a co-lead's assistant), through its maintainer link.
    Maintainer,
    /// The operator, on the loopback plane.
    Operator,
}

/// Why content was refused, in words an assistant can act on.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Invalid(pub String);

impl std::fmt::Display for Invalid {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.0)
    }
}

fn line(s: &str, max: usize, field: &str, required: bool) -> Result<(), Invalid> {
    let t = s.trim();
    if required && t.is_empty() {
        return Err(Invalid(format!("{field} is required")));
    }
    if t.chars().count() > max {
        return Err(Invalid(format!("{field} is at most {max} characters (got {})", t.chars().count())));
    }
    if t.chars().any(char::is_control) {
        return Err(Invalid(format!("{field} must be one line, with no control characters")));
    }
    Ok(())
}

fn paragraphs(s: &str, max: usize, field: &str) -> Result<(), Invalid> {
    if s.trim().chars().count() > max {
        return Err(Invalid(format!("{field} is at most {max} characters (got {})", s.trim().chars().count())));
    }
    if s.chars().any(|c| c.is_control() && c != '\n') {
        return Err(Invalid(format!("{field} may contain line breaks but no other control characters")));
    }
    Ok(())
}

/// An https link, or nothing. Nothing else renders as a link: no `javascript:`, no `data:`,
/// no plain http.
pub fn is_https(url: &str) -> bool {
    let u = url.trim();
    u.len() <= MAX_URL
        && u.starts_with("https://")
        && u.len() > "https://".len()
        && !u.chars().any(|c| c.is_whitespace() || c.is_control() || c == '"' || c == '<' || c == '>')
}

fn link(url: &str, field: &str, required: bool) -> Result<(), Invalid> {
    if url.trim().is_empty() {
        return if required { Err(Invalid(format!("{field} is required"))) } else { Ok(()) };
    }
    if !is_https(url) {
        return Err(Invalid(format!("{field} must be an https:// link of at most {MAX_URL} characters")));
    }
    Ok(())
}

/// A plausible single email address (no display name, no list).
pub fn is_email(s: &str) -> bool {
    let t = s.trim();
    let Some((local, domain)) = t.split_once('@') else { return false };
    !local.is_empty()
        && !domain.contains('@')
        && domain.contains('.')
        && !domain.starts_with('.')
        && !domain.ends_with('.')
        && !t.chars().any(|c| c.is_whitespace() || c.is_control()
            || matches!(c, '<' | '>' | '"' | ',' | ';' | '(' | ')' | '[' | ']' | '\\'))
}

impl PageContent {
    /// Check every field. The limits are maximums, so an assistant that writes long is told
    /// which field and by how much.
    pub fn validate(&self) -> Result<(), Invalid> {
        line(&self.headline, MAX_HEADLINE, "headline", true)?;
        paragraphs(&self.story, MAX_STORY, "story")?;
        for (list, name) in [(&self.next, "next"), (&self.recent, "recent")] {
            if list.len() > MAX_EVENTS {
                return Err(Invalid(format!("{name} has at most {MAX_EVENTS} events")));
            }
            for (i, e) in list.iter().enumerate() {
                let f = |k: &str| format!("{name}[{i}].{k}");
                line(&e.title, MAX_TITLE, &f("title"), true)?;
                line(&e.when, MAX_WHEN, &f("when"), false)?;
                line(&e.place, MAX_WHERE, &f("where"), false)?;
                line(&e.note, MAX_NOTE, &f("note"), false)?;
                link(&e.link, &f("link"), false)?;
            }
        }
        if self.ways_in.len() > MAX_WAYS {
            return Err(Invalid(format!("ways_in has at most {MAX_WAYS} entries")));
        }
        for (i, w) in self.ways_in.iter().enumerate() {
            line(&w.title, MAX_WAY_TITLE, &format!("ways_in[{i}].title"), true)?;
            line(&w.text, MAX_WAY_TEXT, &format!("ways_in[{i}].text"), false)?;
            link(&w.link, &format!("ways_in[{i}].link"), false)?;
        }
        line(&self.contact, MAX_CONTACT, "contact", false)?;
        if !self.contact.trim().is_empty() && !is_email(&self.contact) && !is_https(&self.contact) {
            return Err(Invalid("contact must be one email address or an https:// link".into()));
        }
        if self.links.len() > MAX_LINKS {
            return Err(Invalid(format!("links has at most {MAX_LINKS} entries")));
        }
        for (i, l) in self.links.iter().enumerate() {
            line(&l.label, MAX_LABEL, &format!("links[{i}].label"), true)?;
            link(&l.url, &format!("links[{i}].url"), true)?;
        }
        Ok(())
    }

    /// The same content with surrounding whitespace trimmed, so two submissions that differ
    /// only in padding have one digest.
    pub fn normalized(&self) -> PageContent {
        let ev = |e: &PageEvent| PageEvent {
            title: e.title.trim().into(), when: e.when.trim().into(), place: e.place.trim().into(),
            note: e.note.trim().into(), link: e.link.trim().into(),
        };
        PageContent {
            headline: self.headline.trim().into(),
            story: self.story.trim().replace("\r\n", "\n"),
            next: self.next.iter().map(ev).collect(),
            recent: self.recent.iter().map(ev).collect(),
            ways_in: self.ways_in.iter().map(|w| PageWay {
                title: w.title.trim().into(), text: w.text.trim().into(), link: w.link.trim().into(),
            }).collect(),
            contact: self.contact.trim().into(),
            links: self.links.iter().map(|l| PageLink { label: l.label.trim().into(), url: l.url.trim().into() }).collect(),
            show_committees: self.show_committees,
        }
    }

    /// `sha256:<hex>` over the normalized content's JSON (fields in declaration order).
    pub fn digest(&self) -> String {
        let bytes = serde_json::to_vec(&self.normalized()).expect("page content serializes");
        format!("sha256:{}", web4_core::crypto::sha256_hex(&bytes))
    }
}

/// The brief as stored: trimmed, with `\n` line ends.
pub fn normalize_brief(text: &str) -> String {
    text.replace("\r\n", "\n").trim().to_string()
}

pub fn validate_brief(text: &str) -> Result<(), Invalid> {
    let t = normalize_brief(text);
    if t.is_empty() {
        return Err(Invalid("the brief is empty".into()));
    }
    if t.chars().count() > MAX_BRIEF {
        return Err(Invalid(format!("the brief is at most {MAX_BRIEF} characters (got {})", t.chars().count())));
    }
    if t.chars().any(|c| c.is_control() && c != '\n' && c != '\t') {
        return Err(Invalid("the brief may contain line breaks but no other control characters".into()));
    }
    Ok(())
}

pub fn brief_digest(text: &str) -> String {
    format!("sha256:{}", web4_core::crypto::sha256_hex(normalize_brief(text).as_bytes()))
}

/// The default brief for a chapter.
pub fn default_brief(chapter_name: &str) -> String {
    DEFAULT_BRIEF.replace("{chapter}", chapter_name)
}

/// The digest an undo names when it takes the page back to before anything was published, so
/// the page shows its placeholders again. No content has this digest.
pub const NOTHING_PUBLISHED: &str = "sha256:0000000000000000000000000000000000000000000000000000000000000000";

/// Whether stored page content is the content `sha256` names. The page file is the operator's;
/// the ledger's digest is the record, so content is checked against it each time it's read.
pub fn page_matches(p: &PageContent, sha256: &str) -> bool {
    p.digest() == sha256
}

/// Whether a stored brief is the brief `sha256` names.
pub fn brief_matches(text: &str, sha256: &str) -> bool {
    brief_digest(text) == sha256
}

/// `sha256:` followed by 64 lowercase hex digits.
pub fn is_digest(s: &str) -> bool {
    s.strip_prefix("sha256:").is_some_and(|h| h.len() == 64 && h.chars().all(|c| c.is_ascii_digit() || ('a'..='f').contains(&c)))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn example() -> PageContent {
        serde_json::from_str(include_str!("../../examples/chapter/page-maintainer/page.example.json")).expect("example parses")
    }

    #[test]
    fn the_shipped_example_is_valid_and_its_digest_ignores_padding() {
        let p = example();
        p.validate().expect("example validates");
        let mut padded = p.clone();
        padded.headline = format!("  {}  ", p.headline);
        assert_eq!(p.digest(), padded.digest());
        assert!(is_digest(&p.digest()));
    }

    #[test]
    fn links_are_https_or_nothing() {
        for bad in ["javascript:alert(1)", "http://example.org", "data:text/html,x", "https://", "https://a b", "https://x\"onmouseover=1"] {
            assert!(!is_https(bad), "{bad}");
        }
        let mut p = example();
        p.links[0].url = "javascript:alert(1)".into();
        assert!(p.validate().unwrap_err().0.contains("links[0].url"));
    }

    #[test]
    fn limits_name_the_field_and_unknown_fields_are_refused() {
        let mut p = example();
        p.headline = "x".repeat(MAX_HEADLINE + 1);
        assert!(p.validate().unwrap_err().0.starts_with("headline is at most 90"));
        let mut p = example();
        p.next = vec![p.next[0].clone(); MAX_EVENTS + 1];
        assert!(p.validate().is_err());
        assert!(serde_json::from_str::<PageContent>(r#"{"headline":"x","html":"<script>"}"#).is_err());
    }

    #[test]
    fn contact_is_one_address_or_a_link() {
        let mut p = example();
        for ok in ["chapter@example.org", "https://example.org/contact", ""] {
            p.contact = ok.into();
            p.validate().unwrap_or_else(|e| panic!("{ok}: {e}"));
        }
        for bad in ["a@b.org, c@d.org", "Name <a@b.org>", "not an address", "a@b"] {
            p.contact = bad.into();
            assert!(p.validate().is_err(), "{bad}");
        }
    }

    #[test]
    fn the_default_brief_names_the_chapter_and_validates() {
        let b = default_brief("AI Collective Portland");
        assert!(b.contains("AI Collective Portland's front page"));
        validate_brief(&b).expect("default brief validates");
        assert_eq!(brief_digest(&b), brief_digest(&format!("{b}\n\n")));
    }
}
