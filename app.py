import os
import streamlit as st
from langchain_groq import ChatGroq
from retriever import gen_context
from prompts import answer_template
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from dotenv import load_dotenv

env_loaded = load_dotenv()

st.title("💬 Ecotable Audit Assistant")
st.caption("🚀 Get the information needed for your next audit")


groq_api_key = os.getenv("GROQ_API")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]
  
if "groq_chat" not in st.session_state:
    st.session_state.groq_chat = ChatGroq(temperature=0, groq_api_key = groq_api_key, model_name="llama3-70b-8192")
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferWindowMemory(k=10, memory_key="chat_history", return_messages=True)
    
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "human", "content": prompt})
    st.chat_message("user").write(prompt)
    
    context = gen_context(prompt)

    answer_prompt = PromptTemplate(template=answer_template, input_variables=['context', 'question'])
    formatted_prompt = answer_prompt.format(question=prompt, context=context)
    
    llm_groq = st.session_state.groq_chat
    response = llm_groq.invoke(formatted_prompt).content

    st.session_state.messages.append({"role": "AI", "content": response})
    st.chat_message("assistant").write(response)
    
    

    
    