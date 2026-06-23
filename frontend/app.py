# frontend/app.py

import json
import requests
import streamlit as st

BACKEND = "http://localhost:8000"

st.set_page_config(
    page_title="BA Copilot",
    page_icon="📋",
    layout="wide"
)

# ── Session state ─────────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📋 BA Copilot")
st.caption(
    "Convert business documents into requirements, user stories, "
    "acceptance criteria, and test cases — powered by AI."
)

# ── Input ─────────────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Upload Business Document (PDF, DOCX, TXT)",
    type=["txt", "pdf", "docx"]
)

document_text = st.text_area(
    "Or paste your requirement document here",
    height=250,
    placeholder="Paste BRD, PRD, meeting notes, or any business text…"
)

col1, _ = st.columns([1, 5])

with col1:
    run = st.button("Generate", use_container_width=True)

# ── Generate ──────────────────────────────────────────────────────────────────
if run:

    with st.spinner("Analyzing document…"):
        try:
            if uploaded_file is not None:
                # Send the file directly to the /upload endpoint so the
                # backend's DocumentParser handles PDF/DOCX extraction safely.
                response = requests.post(
                    f"{BACKEND}/upload",
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type or "application/octet-stream"
                        )
                    },
                    timeout=300
                )

            elif document_text.strip():
                response = requests.post(
                    f"{BACKEND}/analyze",
                    json={"document_text": document_text},
                    timeout=300
                )

            else:
                st.warning("Please upload a document or paste text before clicking Generate.")
                st.stop()

            response.raise_for_status()
            st.session_state.result = response.json()

        except requests.exceptions.ConnectionError:
            st.error(
                "Cannot reach the backend at `localhost:8000`. "
                "Make sure the FastAPI server is running:\n\n"
                "```\ncd backend\npython main.py\n```"
            )
            st.stop()
        except requests.exceptions.HTTPError as exc:
            detail = ""
            try:
                detail = exc.response.json().get("detail", "")
            except Exception:
                pass
            st.error(f"Backend error {exc.response.status_code}: {detail or str(exc)}")
            st.stop()
        except Exception as exc:
            st.error(str(exc))
            st.stop()

# ── Results ───────────────────────────────────────────────────────────────────
result = st.session_state.result

if result:

    tabs = st.tabs(["Requirements", "User Stories", "Test Cases", "Review", "Raw JSON"])

    # ── Requirements ──────────────────────────────────────────────────────────
    with tabs[0]:
        requirements = result.get("requirements", {})
        modules = requirements.get("modules", [])

        if not modules:
            st.info("No requirements were extracted.")
        else:
            for module in modules:
                st.subheader(module.get("name", "Unnamed Module"))

                for req in module.get("requirements", []):
                    req_id = req.get("id", "")
                    title = req.get("title", "")
                    description = req.get("description", "")

                    label = f"**{req_id}**" + (f" — {title}" if title else "")
                    st.markdown(label)
                    st.write(description)
                    st.divider()

    # ── User Stories ──────────────────────────────────────────────────────────
    with tabs[1]:
        stories = result.get("stories", {}).get("stories", [])

        if not stories:
            st.info("No user stories were generated.")
        else:
            for story in stories:
                title = story.get("title") or story.get("epic") or "User Story"
                st.subheader(title)
                st.markdown(f"**Epic:** {story.get('epic', '')}")
                st.info(story.get("story", ""))

                criteria = story.get("acceptance_criteria", [])
                if criteria:
                    st.markdown("#### Acceptance Criteria")
                    for item in criteria:
                        # item can be a dict {id, description} or a plain string
                        if isinstance(item, dict):
                            ac_id = item.get("id", "")
                            desc = item.get("description", "")
                            st.markdown(f"- **{ac_id}** {desc}" if ac_id else f"- {desc}")
                        else:
                            st.markdown(f"- {item}")

                st.divider()

    # ── Test Cases ────────────────────────────────────────────────────────────
    with tabs[2]:
        tests = result.get("test_cases", {}).get("test_cases", [])

        if not tests:
            st.info("No test cases were generated.")
        else:
            for test in tests:
                st.subheader(test.get("scenario", "Test Case"))
                st.caption(test.get("type", "").upper())

                preconditions = test.get("preconditions", "")
                if preconditions:
                    st.markdown(f"**Preconditions:** {preconditions}")

                steps = test.get("test_steps", [])
                if steps:
                    st.markdown("**Steps:**")
                    for i, step in enumerate(steps, 1):
                        st.markdown(f"{i}. {step}")

                st.success(f"**Expected Result:** {test.get('expected_result', '')}")
                st.divider()

    # ── Review ────────────────────────────────────────────────────────────────
    with tabs[3]:
        findings = result.get("review", {}).get("findings", [])

        if not findings:
            st.success("✅ No issues found.")
        else:
            st.markdown(f"**Total findings: {len(findings)}**")
            st.divider()

            for finding in findings:
                severity = finding.get("severity", "").upper()

                content = (
                    f"**Category:** {finding.get('category', '')}\n\n"
                    f"**Finding:** {finding.get('finding', '')}\n\n"
                    f"**Recommendation:** {finding.get('recommendation', '')}"
                )

                if severity == "HIGH":
                    st.error(f"🔴 HIGH\n\n{content}")
                elif severity == "MEDIUM":
                    st.warning(f"🟡 MEDIUM\n\n{content}")
                else:
                    st.info(f"🔵 LOW\n\n{content}")

    # ── Raw JSON ──────────────────────────────────────────────────────────────
    with tabs[4]:
        st.json(result)

    # ── Download ──────────────────────────────────────────────────────────────
    st.download_button(
        label="⬇️ Download JSON",
        data=json.dumps(result, indent=2),
        file_name="ba_output.json",
        mime="application/json"
    )
