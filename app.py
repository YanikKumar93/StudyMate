import base64
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agent.nova import createNova
from agent.router import routeRequest
from agent.routing_log import latestRouteDecision
from tools.rag import (
    clear_all_documents,
    delete_document,
    get_active_document,
    get_indexed_documents,
    ingest_document,
    set_active_document,
)

st.set_page_config(
    page_title="StudyMate",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_font_css() -> str:
    """Load local TTF/OTF fonts from ./fonts if available, with Google Fonts fallback."""
    font_dirs = ["./fonts", "./assets/fonts"]
    custom_serif_src = None
    custom_sans_src = None

    for d in font_dirs:
        if os.path.exists(d):
            for fname in sorted(os.listdir(d)):
                lower_name = fname.lower()
                if lower_name.endswith((".ttf", ".otf", ".woff2")):
                    full_p = os.path.join(d, fname)
                    try:
                        with open(full_p, "rb") as f:
                            b64 = base64.b64encode(f.read()).decode("utf-8")
                        fmt = "woff2" if lower_name.endswith(".woff2") else "truetype"
                        src_str = f"url(data:font/{fmt};charset=utf-8;base64,{b64}) format('{fmt}')"

                        if "serif" in lower_name and not custom_serif_src:
                            custom_serif_src = src_str
                        elif "sans" in lower_name and not custom_sans_src:
                            custom_sans_src = src_str
                        elif not custom_serif_src:
                            custom_serif_src = src_str
                    except Exception:
                        pass

    font_face_rules = []
    if custom_serif_src:
        font_face_rules.append(f"""
        @font-face {{
            font-family: 'LocalSerif';
            src: {custom_serif_src};
            font-weight: normal;
            font-style: normal;
        }}
        """)
    if custom_sans_src:
        font_face_rules.append(f"""
        @font-face {{
            font-family: 'LocalSans';
            src: {custom_sans_src};
            font-weight: normal;
            font-style: normal;
        }}
        """)

    serif_family = "'LocalSerif', 'Newsreader', 'Tiempos Text', 'Charter', 'Merriweather', 'Georgia', serif"
    sans_family = "'LocalSans', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"

    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;450;500;600&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400;1,6..72,500&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap');

    {"".join(font_face_rules)}

    html, body, .stApp {{
        font-family: {sans_family};
        letter-spacing: -0.011em;
    }}

    /* Apply typography to text elements while avoiding icon ligatures and code blocks */
    .stApp p, .stApp label, .stApp input, .stApp textarea, .stApp select,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label,
    [data-testid="stChatInput"] textarea, [data-testid="stChatInput"] input,
    .stMarkdown, .stMarkdown p {{
        font-family: {sans_family};
        letter-spacing: -0.011em;
    }}

    /* Preserve and restore Streamlit Material Symbols / Material Icons font */
    [data-testid="stIconMaterial"],
    [data-testid="stExpanderToggleIcon"] *,
    [data-testid="stSidebarCollapseButton"] *,
    [class*="material-symbols"],
    [class*="material-icons"],
    .material-symbols-rounded,
    .material-symbols-outlined,
    .material-symbols-sharp,
    .material-icons,
    i[class*="icon"],
    span[data-testid="stIconMaterial"] {{
        font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
        font-weight: normal !important;
        font-style: normal !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        display: inline-block !important;
        white-space: nowrap !important;
        word-wrap: normal !important;
        direction: ltr !important;
        -webkit-font-smoothing: antialiased !important;
    }}

    header[data-testid="stHeader"] {{
        background: transparent !important;
        pointer-events: auto !important;
    }}

    footer, 
    [data-testid="stStatusWidget"], 
    [data-testid="stFeedback"], 
    div[class*="feedback"],
    div[data-testid*="feedback"],
    div[title*="feedback"],
    iframe[title*="feedback"] {{
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }}

    .block-container {{
        max-width: 780px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 6rem !important;
        margin: 0 auto !important;
    }}

    [data-testid="stChatMessageAvatarUser"],
    [data-testid="stChatMessageAvatarAssistant"],
    [data-testid="stChatMessageAvatarCustom"],
    [data-testid="stChatMessage"] > div:first-child:has(svg),
    [data-testid="stChatMessage"] > div:first-child:has(img) {{
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    [data-testid="stChatMessage"] {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0.2rem 0 !important;
        margin: 0.6rem 0 !important;
        width: 100% !important;
    }}

    [data-testid="stChatMessageContent"] {{
        padding: 0 !important;
        width: 100% !important;
    }}

    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
        display: flex !important;
        justify-content: flex-end !important;
        margin-left: auto !important;
        margin-top: 1.2rem !important;
        margin-bottom: 1.6rem !important;
    }}

    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {{
        display: flex !important;
        justify-content: flex-end !important;
    }}

    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) div[data-testid="stMarkdownContainer"] {{
        background: rgba(128, 128, 128, 0.08) !important;
        border: 1px solid rgba(128, 128, 128, 0.12) !important;
        border-radius: 18px !important;
        padding: 0.65rem 1.15rem !important;
        max-width: 82% !important;
        box-shadow: none !important;
    }}

    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) div[data-testid="stMarkdownContainer"] p {{
        font-family: {sans_family} !important;
        font-size: 0.94rem !important;
        font-weight: 450 !important;
        line-height: 1.55 !important;
        margin: 0 !important;
    }}

    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {{
        display: block !important;
        margin-top: 0.8rem !important;
        margin-bottom: 2.2rem !important;
    }}

    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) div[data-testid="stMarkdownContainer"] {{
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        max-width: 100% !important;
    }}

    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) div[data-testid="stMarkdownContainer"] p,
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) div[data-testid="stMarkdownContainer"] li,
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) div[data-testid="stMarkdownContainer"] blockquote {{
        font-family: {serif_family} !important;
        font-size: 1.08rem !important;
        line-height: 1.8 !important;
        letter-spacing: 0.006em !important;
        margin-bottom: 1.1rem !important;
    }}

    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) div[data-testid="stMarkdownContainer"] h1,
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) div[data-testid="stMarkdownContainer"] h2,
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) div[data-testid="stMarkdownContainer"] h3 {{
        font-family: {serif_family} !important;
        font-weight: 500 !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.6rem !important;
        letter-spacing: -0.015em !important;
    }}

    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) div[data-testid="stMarkdownContainer"] code {{
        font-size: 0.9rem !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        background: rgba(128, 128, 128, 0.1) !important;
    }}

    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) div[data-testid="stMarkdownContainer"] pre {{
        border-radius: 8px !important;
        border: 1px solid rgba(128, 128, 128, 0.15) !important;
        background: rgba(128, 128, 128, 0.05) !important;
    }}

    [data-testid="stChatInput"] {{
        border-radius: 20px !important;
        border: 1px solid rgba(128, 128, 128, 0.22) !important;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.04) !important;
        background: transparent !important;
        transition: border 0.15s ease, box-shadow 0.15s ease;
    }}

    [data-testid="stChatInput"]:focus-within {{
        border-color: rgba(128, 128, 128, 0.45) !important;
        box-shadow: 0 4px 22px rgba(0, 0, 0, 0.07) !important;
    }}

    .context-tag {{
        display: inline-block;
        font-size: 0.74rem;
        color: rgba(128, 128, 128, 0.9);
        letter-spacing: 0.02em;
        text-transform: uppercase;
        margin-bottom: 1.5rem;
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
        padding-bottom: 4px;
    }}
    </style>
    """


st.markdown(get_font_css(), unsafe_allow_html=True)


def visibleMessages(chat: list) -> list:
    return [
        message
        for message in chat
        if message.get("role") in ("user", "assistant") and message.get("content")
    ]


def startChat() -> None:
    if "chat" not in st.session_state:
        st.session_state.chat = createNova()


try:
    startChat()
except Exception as error:
    st.error(f"Initialization error: {error}")
    st.info("Check your .env API key / base URL / model settings.")
    st.stop()


with st.sidebar:
    st.subheader("Knowledge Base")
    st.caption("Upload documents to ground NOVA's answers.")

    with st.expander("Upload Document", expanded=True):
        uploaded_file = st.file_uploader(
            "Select file",
            type=["pptx", "pdf", "txt", "md"],
            key="file_uploader",
            label_visibility="collapsed",
        )

        if uploaded_file is not None:
            if st.button("Index Document", use_container_width=True, type="primary"):
                with st.spinner("Processing text and embeddings..."):
                    try:
                        os.makedirs("./temp_uploads", exist_ok=True)
                        save_path = os.path.join("./temp_uploads", uploaded_file.name)
                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        result = ingest_document(save_path)
                        if str(result).lower().startswith("failed") or str(result).lower().startswith("error"):
                            st.error(result)
                        else:
                            st.success(result)
                            st.rerun()
                    except Exception as error:
                        st.error(f"Upload failed: {error}")

    st.divider()

    indexed_docs = get_indexed_documents()
    st.subheader("Indexed Files")

    if not indexed_docs:
        st.caption("No documents indexed.")
    else:
        doc_names = [d["filename"] for d in indexed_docs]
        options = ["All Documents"] + doc_names

        curr_active = get_active_document()
        default_index = 0
        if curr_active in doc_names:
            default_index = options.index(curr_active)

        selected_scope = st.selectbox(
            "Search scope",
            options=options,
            index=default_index,
            help="Choose whether queries search across all materials or focus on a single document.",
        )
        if selected_scope == "All Documents":
            set_active_document("")
        else:
            set_active_document(selected_scope)

        for doc in indexed_docs:
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{doc['filename']}**")
                st.caption(f"{doc['chunks']} chunks")
            with c2:
                if st.button("Delete", key=f"del_{doc['filename']}", help="Remove from index"):
                    delete_document(doc["filename"])
                    st.rerun()

        if st.button("Clear All Files", use_container_width=True):
            clear_all_documents()
            st.rerun()

    st.divider()

    st.subheader("Session")
    lastRoute = st.session_state.get("last_route", {})
    if lastRoute:
        r_type = lastRoute.get("route", "unknown")
        latency = lastRoute.get("latencyMs", 0)
        tool = lastRoute.get("tool", "")
        if r_type == "system_tool" and tool:
            st.caption(f"Last Route: Direct Tool ({tool}) | {latency}ms")
        elif r_type == "agent":
            st.caption(f"Last Route: Agent (LLM) | {latency}ms")
        else:
            st.caption(f"Last Route: {r_type} | {latency}ms")
    else:
        st.caption("Ready")

    if st.button("Reset Conversation", use_container_width=True):
        st.session_state.chat = createNova()
        st.session_state.pop("last_route", None)
        st.rerun()


st.title("NOVA")

active_doc = get_active_document()
indexed_docs = get_indexed_documents()

if indexed_docs:
    scope_text = f"Scope: {active_doc}" if active_doc else "Scope: All Indexed Documents"
    total_chunks = sum(d["chunks"] for d in indexed_docs)
    st.markdown(f'<div class="context-tag">{scope_text} &bull; {total_chunks} chunks</div>', unsafe_allow_html=True)

for message in visibleMessages(st.session_state.chat):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_message = st.chat_input("Ask a question or query uploaded documents...")
if user_message:
    with st.chat_message("user"):
        st.markdown(user_message)

    with st.chat_message("assistant"):
        with st.spinner(""):
            try:
                response = routeRequest(
                    user_message,
                    st.session_state.chat,
                    medium="app",
                )
                st.session_state.last_route = latestRouteDecision()
                if not response or not str(response).strip():
                    response = "I couldn't generate a reply just now. Please try again."
                st.markdown(response)
            except Exception as error:
                st.error("An unexpected error occurred.")
                st.caption(f"Details: {type(error).__name__}: {error}")
