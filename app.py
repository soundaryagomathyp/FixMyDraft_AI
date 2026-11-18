import streamlit as st
import re
import io

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

    if "₹" in claim or "rs." in claim_lower or "inr" in claim_lower:
        keywords = ["price", "pricing", "discount", "offer", "amount"]

    elif "%" in claim:
        keywords = ["percentage", "performance", "improvement", "results", "claims"]

    elif re.search(r"customers|users|clients", claim_lower):
        keywords = ["customers", "users", "clients", "statistics", "numbers"]

    elif re.search(r"hours|days|years", claim_lower):
        keywords = ["hours", "days", "years", "delivery", "time", "deadline"]

    elif re.search(r"certified|award-winning", claim_lower):
        keywords = ["certified", "certification", "award", "recognition"]

    else:
        keywords = []

    sources = [
        ("Approved Facts and Rules", profile["rules"]),
        ("Uploaded PDF Guidelines", profile["pdf_guidelines"])
    ]

    for source_name, source_text in sources:

        for line in source_text.splitlines():

            line = line.strip()

            if line and any(
                keyword in line.lower()
                for keyword in keywords
            ):

                return source_name, line

    return (
        "No matching guideline found",
        "No explicit supporting guideline was found. Human review is required."
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

        approved = profile["approved_words"].splitlines()

        missing_words = []

        for word in approved:

            word = word.strip()

            if word and word.lower() not in content.lower():

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

        st.download_button(
            label="📥 Download Compliance Report",
            data=pdf_report,
            file_name="Brand_Compliance_Report.pdf",
            mime="application/pdf"
        )