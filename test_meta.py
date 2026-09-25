import streamlit as st
import base64

st.title("Test Meta Refresh")

if st.button("Download"):
    pdf = b"%PDF-1.4\n1 0 obj\n<<\n/Title (Hello)\n>>\nendobj\n"
    b64 = base64.b64encode(pdf).decode()
    st.markdown(f'<meta http-equiv="refresh" content="0;url=data:application/pdf;base64,{b64}">', unsafe_allow_html=True)
