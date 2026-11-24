import streamlit as st
import re
import io
import json
import os
from datetime import datetime
from pypdf import PdfReader

from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


# ----------------------------------
# FUNCTION 1: COMBINE BRAND GUIDELINES
# ----------------------------------

def build_combined_guidelines(profile):

    sections = []

    sections.append("BRAND TONE:\n" + profile["tone"])

    if profile["pdf_guidelines"].strip():
        sections.append(
            "COMPANY PDF GUIDELINES:\n" + profile["pdf_guidelines"]
        )

    if profile["approved_words"].strip():
        sections.append(
            "APPROVED TERMINOLOGY:\n" + profile["approved_words"]
        )

    if profile["avoided_words"].strip():
        sections.append(
            "TERMS TO AVOID:\n" + profile["avoided_words"]
        )

    if profile["rules"].strip():
        sections.append(
            "APPROVED FACTS AND RULES:\n" + profile["rules"]
        )

    return "\n\n".join(sections)


# ----------------------------------
# FUNCTION 2: CLAIM EXPLANATION
# ----------------------------------

def get_claim_explanation(claim):

    claim = claim.lower()

    if "₹" in claim or "rs." in claim or "inr" in claim:
        return "Price information requires company approval."

    elif "%" in claim:
        return "Performance promises or percentage claims must be verified."

    elif re.search(r"customers|users|clients", claim):
        return "Customer statistics must be approved by the company."

    elif re.search(r"hours|days|years", claim):
        return "Time-related promises must be verified against approved company facts."

    elif re.search(r"certified|award-winning", claim):
        return "Certifications and awards require official verification."

    else:
        return "This claim requires human review."

# ----------------------------------
# FUNCTION: SUGGEST CORRECTIONS
# ----------------------------------

def suggest_correction(text):

    suggestions = []

    replacements = {
        "gonna": "going to",
        "wanna": "want to",
        "awesome": "excellent",
        "hey": "hello",
        "hereby": "in this message"
    }

    corrected_text = text

    for old_word, new_word in replacements.items():

        pattern = re.compile(
            r"\b" + re.escape(old_word) + r"\b",
            re.IGNORECASE
        )

        corrected_text = pattern.sub(
            new_word,
            corrected_text
        )

    if corrected_text != text:

        suggestions.append(corrected_text)

    return suggestions


# ----------------------------------
# FUNCTION 3: GENERATE PDF REPORT
# ----------------------------------

def generate_compliance_pdf(
    profile,
    draft,
    violations,
    missing_words,
    tone_issues,
    unsupported_claims,
    claim_evidence
):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4
    )

    styles = getSampleStyleSheet()

    elements = []

    # Helper to safely display user-entered text in PDF
    def add_text(text, style):

        safe_text = escape(str(text))
        safe_text = safe_text.replace("₹", "INR ")

        elements.append(
            Paragraph(safe_text, style)
        )

    # Report title

    add_text("FixMyDraft_AI", styles["Title"])

    add_text("Brand Compliance Report", styles["Heading1"])

    elements.append(Spacer(1, 15))

    # Basic details

    add_text(
        "Organisation: " + profile["company"],
        styles["Normal"]
    )

    add_text(
        "Draft Title: " + draft["title"],
        styles["Normal"]
    )

    add_text(
        "Content Type: " + draft["content_type"],
        styles["Normal"]
    )

    elements.append(Spacer(1, 15))

    # 1. Avoided words

    add_text("1. Avoided Words", styles["Heading2"])

    if violations:

        for word in violations:

            add_text(
                "Detected: " + word,
                styles["Normal"]
            )

    else:

        add_text(
            "No avoided words detected.",
            styles["Normal"]
        )

    elements.append(Spacer(1, 10))

    # 2. Missing approved terminology

    add_text(
        "2. Missing Approved Terminology",
        styles["Heading2"]
    )

    if missing_words:

        for word in missing_words:

            add_text(
                "Missing: " + word,
                styles["Normal"]
            )

    else:

        add_text(
            "All approved terms satisfied.",
            styles["Normal"]
        )

    elements.append(Spacer(1, 10))

    
    # 3. Unsupported claims

    add_text(
        "3. Unsupported Claims Review",
        styles["Heading2"]
    )

    if unsupported_claims:

        for claim, source_name, evidence in claim_evidence:

            explanation = get_claim_explanation(claim)

            add_text(
                "Claim: " + claim,
                styles["Normal"]
            )

            add_text(
                "Reason: " + explanation,
                styles["Normal"]
            )

            add_text(
                "Guideline Source: " + source_name,
                styles["Normal"]
            )

            add_text(
                "Matching Evidence: " + evidence,
                styles["Normal"]
            )

            elements.append(Spacer(1, 8))

    else:

        add_text(
            "No obvious unsupported claims detected.",
            styles["Normal"]
        )

    elements.append(Spacer(1, 10))


    # 4. Brand tone

    add_text(
        "4. Brand Tone Analysis",
        styles["Heading2"]
    )

    if tone_issues:

        for issue in tone_issues:

            add_text(
                "Possible tone mismatch: " + issue,
                styles["Normal"]
            )

    else:

        add_text(
            "No obvious tone mismatches detected.",
            styles["Normal"]
        )

    doc.build(elements)

    buffer.seek(0)

    return buffer.getvalue()


# ----------------------------------
# STREAMLIT PAGE SETTINGS
# ----------------------------------

st.set_page_config(
    page_title="FixMyDraft_AI",
    page_icon="🛡️",
    layout="wide"
)

st.markdown("""
<style>

/* Main page background */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(
        135deg,
        #F0FDFA 0%,
        #D9F7F4 45%,
        #B9F0EC 100%
    );
}

/* Main content area */
[data-testid="stMain"] {
    background: transparent;
}

/* Header */
[data-testid="stHeader"] {
    background: rgba(240, 253, 250, 0.75);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #B9F0EC 0%,
        #D9F7F4 100%
    );
}

/* Main headings */
h1, h2, h3 {
    color: #164E63 !important;
}

/* Normal text */
p, label, li {
    color: #164E63;
}


/* Buttons - Ocean Teal */
.stButton > button {
    background-color: #087E8B !important;
    color: #FFFFFF !important;
    border: 1px solid #087E8B !important;
    border-radius: 12px;
    padding: 0.55rem 1.2rem;
    font-weight: 600;
}

/* Force button text to remain white */
.stButton > button p,
.stButton > button span {
    color: #FFFFFF !important;
}

/* Button hover - Bright Cyan */
.stButton > button:hover {
    background-color: #2DD4D8 !important;
    color: #073B4C !important;
    border: 1px solid #2DD4D8 !important;
}

/* Hover text */
.stButton > button:hover p,
.stButton > button:hover span {
    color: #073B4C !important;
}


/* Button hover */
.stButton > button:hover {
    background-color: #2DD4D8;
    color: #073B4C;
    border: 1px solid #2DD4D8;
    transform: translateY(-2px);
}

/* Text input and text area */
.stTextInput input,
.stTextArea textarea {
    background-color: #FFFFFF;
    border: 1px solid #B9F0EC;
    border-radius: 10px;
}

/* Select boxes */
.stSelectbox div[data-baseweb="select"] {
    background-color: #FFFFFF;
    border-radius: 10px;
}

/* Download button */
.stDownloadButton > button {
    background-color: #164E63;
    color: white;
    border-radius: 12px;
}

/* Success messages */
[data-testid="stAlert"] {
    border-radius: 12px;
}

/* Floating white cards */
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: rgba(255, 255, 255, 0.94);
    border: 1px solid #D5EAE8;
    border-radius: 18px;
    box-shadow: 0 5px 18px rgba(8, 126, 139, 0.10);
    padding: 12px;
}

/* ----------------------------------
   OCEAN BREEZE ANIMATIONS
---------------------------------- */

/* Gentle page fade-in */
@keyframes oceanFadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

[data-testid="stMain"] {
    animation: oceanFadeIn 0.7s ease-out;
}

/* Floating card hover effect */
[data-testid="stVerticalBlockBorderWrapper"] {
    transition:
        transform 0.25s ease,
        box-shadow 0.25s ease;
}

[data-testid="stVerticalBlockBorderWrapper"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 9px 24px rgba(8, 126, 139, 0.16);
}

/* Smooth button animation */
.stButton > button {
    transition:
        background-color 0.25s ease,
        color 0.25s ease,
        transform 0.2s ease,
        box-shadow 0.25s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 14px rgba(8, 126, 139, 0.20);
}

/* Soft title glow */
h1 {
    text-shadow: 0 2px 12px rgba(45, 212, 216, 0.18);
}

/* Respect users who prefer reduced motion */
@media (prefers-reduced-motion: reduce) {
    [data-testid="stMain"],
    [data-testid="stVerticalBlockBorderWrapper"],
    .stButton > button {
        animation: none !important;
        transition: none !important;
        transform: none !important;
    }
}

/* ----------------------------------
   STAGE 4 - COMPLIANCE REPORT
---------------------------------- */

/* Keep the main report area light */
[data-testid="stMain"] {
    background: #F0FDFA !important;
}

/* Make headings readable */
[data-testid="stMain"] h1,
[data-testid="stMain"] h2,
[data-testid="stMain"] h3 {
    color: #164E63 !important;
}

/* Report text */
[data-testid="stMain"] p,
[data-testid="stMain"] label,
[data-testid="stMain"] li {
    color: #164E63 !important;
}

/* Report cards and bordered sections */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important;
    border: 1px solid #B9F0EC !important;
    border-radius: 18px !important;
    box-shadow: 0 5px 18px rgba(8, 126, 139, 0.10);
}

/* Human Review and Approval section */
[data-testid="stMain"] [data-testid="stAlert"] {
    background: #E7F8F6 !important;
    border-radius: 12px;
}

/* Stage 4 buttons */
[data-testid="stMain"] .stButton > button {
    background: #087E8B !important;
    color: #FFFFFF !important;
}

/* Keep button text white */
[data-testid="stMain"] .stButton > button p {
    color: #FFFFFF !important;
}


</style>
""", unsafe_allow_html=True)


# ----------------------------------
# MAIN WEBSITE HEADING
# ----------------------------------

st.markdown("""
# 🛡️ FixMyDraft_AI

### Every Draft. On Brand. Every Time.

An intelligent brand governance platform that checks content before publication.
""")

# YOUR STAGE 1 CODE STARTS BELOW

#===============
# STAGE 1: BRAND PROFILE
# ==================================

st.header("🏢 Brand Profile")

st.write(
    "Enter your organisation's approved brand guidelines."
)

guideline_file = st.file_uploader(
    "Upload Brand Guidelines (PDF)",
    type=["pdf"]
)

company_name = st.text_input("Organisation Name")

brand_tone = st.selectbox(
    "Choose your brand tone",
    ["Professional", "Friendly", "Formal", "Casual"]
)

approved_words = st.text_area(
    "Approved Terminology",
    placeholder="Enter approved words or phrases, one per line."
)

avoided_words = st.text_area(
    "Words or Phrases to Avoid",
    placeholder="Enter words or phrases that should not be used."
)

brand_rules = st.text_area(
    "Approved Facts and Messaging Rules",
    placeholder="Enter your organisation's approved facts and rules."
)


if st.button("Save Brand Profile"):

    if company_name.strip():

        pdf_text = ""

        if guideline_file is not None:

            try:

                reader = PdfReader(guideline_file)

                for page in reader.pages:

                    pdf_text += (page.extract_text() or "") + "\n"

            except Exception as error:

                st.error("Could not read the uploaded PDF.")
                st.caption(str(error))

        st.session_state["brand_profile"] = {

            "company": company_name,
            "tone": brand_tone,
            "approved_words": approved_words,
            "avoided_words": avoided_words,
            "rules": brand_rules,
            "pdf_guidelines": pdf_text

        }

        st.session_state["brand_profile"]["combined_guidelines"] = (
            build_combined_guidelines(
                st.session_state["brand_profile"]
            )
        )

        st.success("Brand Profile Saved Successfully!")

        if pdf_text.strip():

            st.success("PDF Guidelines Extracted Successfully!")

        elif guideline_file is not None:

            st.warning(
                "No readable text found in the PDF. "
                "It may be a scanned document."
            )

    else:

        st.error("Please enter your organisation name.")


# DISPLAY SAVED BRAND PROFILE

if "brand_profile" in st.session_state:

    st.subheader("Saved Brand Profile")

    st.json(st.session_state["brand_profile"])

    if st.session_state["brand_profile"]["pdf_guidelines"]:

        st.subheader("📄 Extracted PDF Guidelines")

        st.text_area(
            "Text extracted from uploaded PDF",
            value=st.session_state["brand_profile"]["pdf_guidelines"],
            height=300,
            disabled=True
        )

    st.subheader("📋 Combined Guidelines for Checking")

    st.text_area(
        "Guidelines the app will use",
        value=st.session_state["brand_profile"]["combined_guidelines"],
        height=300,
        disabled=True
    )


# ==================================
# STAGE 2: DRAFT SUBMISSION
# ==================================

st.divider()

st.header("📝 Draft Submission")

st.write(
    "Enter the content you want to check "
    "against your organisation's brand guidelines."
)

draft_title = st.text_input(
    "Draft Title",
    placeholder="e.g. Summer Sale Advertisement"
)

content_type = st.selectbox(
    "Select Content Type",
    [
        "Instagram Post",
        "Advertisement",
        "Email",
        "Website Content",
        "Blog Post",
        "Other"
    ]
)

draft_content = st.text_area(
    "Enter Your Draft",
    placeholder="Paste your content here...",
    height=200
)


if st.button("Submit Draft"):

    if draft_title.strip() and draft_content.strip():

        st.session_state["draft"] = {

            "title": draft_title,
            "content_type": content_type,
            "content": draft_content

        }

        st.success("Draft Submitted Successfully!")

    else:

        st.error("Please enter both the draft title and content.")


# DISPLAY SUBMITTED DRAFT

if "draft" in st.session_state:

    st.subheader("📄 Submitted Draft")

    st.write(
        "**Title:**",
        st.session_state["draft"]["title"]
    )

    st.write(
        "**Content Type:**",
        st.session_state["draft"]["content_type"]
    )

    st.write("**Draft Content:**")

    st.info(st.session_state["draft"]["content"])

# ----------------------------------
# FUNCTION 2B: FIND GUIDELINE EVIDENCE
# ----------------------------------


def find_guideline_evidence(profile, claim):

    claim_lower = claim.lower()

    # Identify the type of claim and related guideline terms
    if "₹" in claim or "rs." in claim_lower or "inr" in claim_lower:
        category = "Price"
        search_terms = {
            "price", "prices", "pricing", "cost", "amount",
            "discount", "offer", "fee", "charge", "approved",
            "approval", "verify", "verified"
        }

    elif "%" in claim:
        category = "Percentage or performance"
        search_terms = {
            "percentage", "percent", "performance", "improvement",
            "results", "claims", "claim", "guarantee",
            "guarantees", "satisfaction", "approved", "approval",
            "verified", "verify"
        }

    elif re.search(r"customers|users|clients", claim_lower):
        category = "Customer statistics"
        search_terms = {
            "customer", "customers", "user", "users",
            "client", "clients", "statistics", "statistic",
            "numbers", "number", "count", "approved",
            "approval", "verify", "verified"
        }

    elif re.search(r"hours|days|years", claim_lower):
        category = "Time-related claim"
        search_terms = {
            "time", "hours", "days", "years", "timeline",
            "support", "response", "delivery", "deadline",
            "service", "accurate", "approved", "approval",
            "verify", "verified"
        }

    elif re.search(r"certified|certification|award", claim_lower):
        category = "Certification or award"
        search_terms = {
            "certified", "certification", "certificate",
            "certificates", "award", "awards", "recognition",
            "qualified", "official", "valid", "document",
            "documents", "approved", "approval", "verify",
            "verified"
        }

    else:
        category = "General claim"

        claim_words = set(
            re.findall(r"\b[a-zA-Z]+\b", claim_lower)
        )

        stop_words = {
            "the", "a", "an", "is", "are", "was", "were",
            "our", "we", "you", "your", "and", "or", "to",
            "of", "in", "on", "for", "with", "this", "that",
            "has", "have", "had", "it", "its", "by", "from"
        }

        search_terms = claim_words - stop_words

    # Collect guideline sources
    sources = [
        (
            "Approved Facts and Rules",
            profile.get("rules", "")
        ),
        (
            "Uploaded PDF Guidelines",
            profile.get("pdf_guidelines", "")
        )
    ]

    best_match = None
    best_score = 0
    best_terms = []

    # Compare each guideline line with the claim category
    for source_name, source_text in sources:

        if not isinstance(source_text, str):
            continue

        for line in source_text.splitlines():

            line = line.strip()

            if not line:
                continue

            guideline_words = set(
                re.findall(r"\b[a-zA-Z]+\b", line.lower())
            )

            matched_terms = search_terms & guideline_words
            score = len(matched_terms)

            if score > best_score:
                best_score = score
                best_match = (source_name, line)
                best_terms = sorted(matched_terms)

    # Return the strongest relevant guideline
    if best_match and best_score >= 1:

        source_name, guideline = best_match

        explanation = (
            f"Claim category: {category}\n"
            "Matching terms: "
            + ", ".join(best_terms)
            + "\nPlease confirm that this guideline applies "
              "to the claim. Human review is recommended."
        )

        return source_name, guideline + "\n\n" + explanation

    return (
        "No sufficiently relevant guideline found",
        f"Claim category: {category}\n"
        "No relevant guideline passage was found. "
        "Human review is required."
    )



# ==================================
# STAGE 3: BRAND COMPLIANCE CHECKING
# ==================================

st.divider()

st.header("🔍 Brand Compliance Checker")

st.write("Check your draft against company guidelines.")


if st.button("Check Brand Compliance"):

    if "brand_profile" not in st.session_state:

        st.error("Please save your Brand Profile first.")

    elif "draft" not in st.session_state:

        st.error("Please submit a draft first.")

    else:

        profile = st.session_state["brand_profile"]

        draft = st.session_state["draft"]

        content = draft["content"]


        # ----------------------------------
        # CHECK UNSUPPORTED CLAIMS
        # ----------------------------------

        claim_patterns = [

            r"(?:₹|rs\.?|inr)\s?\d[\d,]*(?:\.\d+)?",

            r"\b\d+(?:\.\d+)?\s?%",

            r"\b\d[\d,]*\s+(?:customers|users|clients|hours|days|years)\b",

            r"\b(?:ISO certified|award-winning|certified)\b"

        ]

        unsupported_claims = []
        claim_evidence = []

        for pattern in claim_patterns:

            matches = re.findall(
                pattern,
                content,
                re.IGNORECASE
            )

            unsupported_claims.extend(matches)


        # ----------------------------------
        # CHECK AVOIDED WORDS
        # ----------------------------------

        avoided = profile["avoided_words"].splitlines()

        violations = []

        for word in avoided:

            word = word.strip()

            if word and word.lower() in content.lower():

                violations.append(word)


       
        # ----------------------------------
        # CHECK APPROVED TERMINOLOGY
        # ----------------------------------

        approved = profile.get("approved_words", "").splitlines()

        missing_words = []

        content_lower = content.lower()

        for word in approved:

            word = word.strip()

            if not word:
                continue

            # Normalize hyphens to spaces for comparison
            normalized_word = re.sub(r"[-_]", " ", word.lower())
            normalized_content = re.sub(r"[-_]", " ", content_lower)

            # Check whether the approved term appears
            if normalized_word not in normalized_content:
                missing_words.append(word)


        # ----------------------------------
        # CHECK BRAND TONE
        # ----------------------------------

        brand_tone = profile["tone"]

        tone_words = {

            "Professional": ["awesome", "gonna", "wanna"],

            "Friendly": ["hereby", "aforementioned", "pursuant"],

            "Formal": ["hey", "gonna", "wanna"],

            "Casual": ["hereby", "therefore", "aforementioned"]

        }

        tone_issues = []

        for word in tone_words.get(brand_tone, []):

            if word.lower() in content.lower():

                tone_issues.append(word)


        # ----------------------------------
        # READ PDF GUIDELINES
        # ----------------------------------

        pdf_guidelines = profile["pdf_guidelines"]

        pdf_results = []

        if pdf_guidelines.strip():

            pdf_lines = pdf_guidelines.splitlines()

            for line in pdf_lines:

                line = line.strip()

                if line:

                    pdf_results.append(line)


        # ----------------------------------
        # CHECK COMPANY RULES
        # ----------------------------------

        company_rules = profile["rules"].splitlines()

        rule_results = []

        for rule in company_rules:

            rule = rule.strip()

            if rule:

                rule_results.append(rule)

        # ----------------------------------
        # CORRECTION SUGGESTIONS
        # ----------------------------------

        st.subheader("💡 Correction Suggestions")

        suggestions = suggest_correction(content)

        if suggestions:

            for suggestion in suggestions:

                st.info("Suggested revised draft:")

                st.write(suggestion)

        else:

            st.success(
                "No basic wording corrections suggested."
            )


        # ----------------------------------
        # DISPLAY TONE RESULTS
        # ----------------------------------

        st.subheader("🎨 Brand Tone Analysis")

        st.write("Selected Brand Tone:", brand_tone)

        if tone_issues:

            st.warning("Possible tone mismatches detected!")

            for word in tone_issues:

                st.write("⚠️", word)

        else:

            st.success("No obvious tone mismatches detected!")


        # ----------------------------------
        # DISPLAY COMPANY RULES
        # ----------------------------------

        if rule_results:

            st.subheader("📋 Company Rules")

            for rule in rule_results:

                st.info("Rule to be reviewed: " + rule)


        # ----------------------------------
        # DISPLAY PDF GUIDELINES
        # ----------------------------------

        if pdf_results:

            st.subheader("📄 PDF Guideline Review")

            st.info(
                "The following guidelines were extracted "
                "from the company's PDF and are ready for review."
            )

            for guideline in pdf_results:

                st.write("📌", guideline)

        else:

            st.info("No PDF guidelines available for checking.")


       
        # ----------------------------------
        # DISPLAY UNSUPPORTED CLAIMS
        # ----------------------------------

        st.subheader("🚩 Unsupported Claims Review")

        if unsupported_claims:

            st.warning(
                "Possible claims requiring company approval were detected."
            )

            for claim in unsupported_claims:

                st.write("⚠️", claim)

                st.caption(
                    "Reason: " + get_claim_explanation(claim)
                )

                source_name, evidence = find_guideline_evidence(
                    profile,
                    claim
                )
                claim_evidence.append(
                    (claim, source_name, evidence)
                )

                st.write("📚 Guideline Evidence:", source_name)

                st.info(evidence)

            st.info(
                "These claims are not automatically false. "
                "A company reviewer should verify them."
            )

        else:

            st.success("No obvious unsupported claims detected!")

        # ----------------------------------
        # DISPLAY COMPLIANCE RESULTS
        # ----------------------------------

        st.subheader("📊 Compliance Results")

        if violations:

            st.error("❌ Avoided words detected!")

            for word in violations:

                st.write("❌", word)

        else:

            st.success("No avoided words detected!")


        if missing_words:

            st.warning("Some approved terminology is missing.")

            for word in missing_words:

                st.write("⚠️", word)

        else:

            st.success("Approved terminology requirements satisfied!")


        # ==================================
        # STAGE 4: DOWNLOAD COMPLIANCE REPORT
        # ==================================

        st.divider()

        st.header("📄 Stage 4: Compliance Report")

        pdf_report = generate_compliance_pdf(
            profile,
            draft,
            violations,
            missing_words,
            tone_issues,
            unsupported_claims,
            claim_evidence
        )

        # ----------------------------------
        # SAVE COMPLIANCE RESULTS FOR REVIEW
        # ----------------------------------

        st.session_state["compliance_results"] = {
            "profile": profile,
            "draft": draft,
            "violations": violations,
            "missing_words": missing_words,
            "tone_issues": tone_issues,
            "unsupported_claims": unsupported_claims,
            "claim_evidence": claim_evidence,
            "suggestions": suggestions,
            "rule_results": rule_results,
            "pdf_results": pdf_results,
            "pdf_report": pdf_report
        }

 
        st.download_button(
            label="📥 Download Compliance Report",
            data=pdf_report,
            file_name="Brand_Compliance_Report.pdf",
            mime="application/pdf"
        )

# ==================================
# ROUND 3: HUMAN REVIEW WORKFLOW
# ==================================

if "compliance_results" in st.session_state:

    st.divider()

    st.header("👩‍💼 Human Review and Approval")

    results = st.session_state["compliance_results"]

    st.info(
        "A reviewer should examine the compliance findings "
        "before making the final decision."
    )

    st.subheader("📋 Review Summary")

    st.write(
        "Draft submitted:",
        results["draft"]["content"][:300]
    )

    st.write(
        "Possible unsupported claims:",
        len(results["unsupported_claims"])
    )

    st.write(
        "Avoided words detected:",
        len(results["violations"])
    )

    st.write(
        "Missing approved words:",
        len(results["missing_words"])
    )

    st.divider()

    reviewer_name = st.text_input(
        "Reviewer Name",
        key="reviewer_name"
    )

    review_decision = st.radio(
        "Review Decision",
        ["Approved", "Requires Changes"],
        key="review_decision"
    )

    reviewer_comments = st.text_area(
        "Reviewer Comments",
        key="reviewer_comments"
    )
    
    if st.button("Submit Review"):

        if not reviewer_name.strip():

            st.error("Please enter the reviewer name.")

        elif not reviewer_comments.strip():

            st.error("Please enter review comments.")

        else:

            review_record = {
                "reviewer": reviewer_name.strip(),
                "decision": review_decision,
                "comments": reviewer_comments.strip(),
                "draft": results["draft"]["content"],
                "reviewed_at": datetime.now().astimezone().isoformat(
                    timespec="seconds"
                )
            }

            st.session_state["review_record"] = review_record

            history_file = os.path.join(
                os.path.dirname(__file__),
                "review_history.json"
            )

            if os.path.exists(history_file):

                with open(history_file, "r", encoding="utf-8") as file:
                    review_history = json.load(file)

            else:

                review_history = []

            review_history.append(review_record)

            with open(history_file, "w", encoding="utf-8") as file:
                json.dump(
                    review_history,
                    file,
                    indent=4,
                    ensure_ascii=False
                )

            st.success("Review submitted and saved to history!")


    

       

           
    if "review_record" in st.session_state:

        review = st.session_state["review_record"]

        st.subheader("📌 Final Review Status")

        st.write("Reviewer:", review["reviewer"])

        st.write("Decision:", review["decision"])

        st.write("Comments:", review["comments"])

        if review["decision"] == "Approved":

            st.success("Draft approved by the reviewer.")

        else:

            st.warning("Draft requires changes.")

# ==================================
# REVIEW HISTORY AND AUDIT TRAIL
# ==================================

st.divider()

st.subheader("📚 Review History")

history_file = "review_history.json"

if os.path.exists(history_file):

    with open(history_file, "r", encoding="utf-8") as file:
        review_history = json.load(file)

    if review_history:

        for index, record in enumerate(
            reversed(review_history),
            start=1
        ):

            with st.expander(
                f"Review {index} - {record['decision']}"
            ):

                st.write("Reviewer:", record["reviewer"])

                st.write("Date and Time:", record["reviewed_at"])

                st.write("Decision:", record["decision"])

                st.write("Comments:", record["comments"])

                st.text_area(
                    "Reviewed Draft",
                    value=record["draft"],
                    height=150,
                    disabled=True,
                    key=f"history_draft_{index}"
                )

    else:

        st.info("No review history available yet.")

else:

    st.info("No review history available yet.")

