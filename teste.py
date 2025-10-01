import streamlit as st

st.title("Teste Streamlit")
st.write("Se voce esta vendo isso, o Streamlit esta funcionando!")

if st.button("Clique aqui"):
    st.success("Botao funcionando!")