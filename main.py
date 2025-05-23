import streamlit as st
from azure.storage.blob import BlobServiceClient
import os
import pymssql
import uuid
import json
from dotenv import load_dotenv
load_dotenv()


blobconnectiongstring = os.getenv("BLOB_CONNECTION_STRING")
blobcontainername = os.getenv("BLOB_CONTAINER_NAME")
blobaccountname = os.getenv("BLOB_ACCOUNT_NAME")

SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DATABASE = os.getenv("SQL_DATABASE")
SQL_USER = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")

st.title('Cadastro de Produtos')

#formulario de cadastro de produtos

product_name = st.text_input('Nome do Produto')
product_price = st.number_input('Preço do Produto', min_value=0.0, format='%.2f')
product_description = st.text_area('Descrição do Produto')
product_image = st.file_uploader('Imagem do Produto', type=['jpg','png','jpeg'])

#save image to blob storage
def upload_image(file):
    blob_service_client = BlobServiceClient.from_connection_string(blobconnectiongstring)
    container_client = blob_service_client.get_container_client(blobcontainername)
    blob_name = str(uuid.uuid4()) + file.name
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(file.read(),overwrite=True)
    image_url = f"https://{blobaccountname}.blob.core.windows.net/{blobcontainername}/{blob_name}"
    return image_url
#save product to sql server
def insert_product(name, price, description, file):
    try:
        # Faz o upload da imagem e obtém a URL
        image_url = upload_image(file)

        # Conexão com o banco de dados
        conn = pymssql.connect(
            server=SQL_SERVER,
            user=SQL_USER,
            password=SQL_PASSWORD,
            database=SQL_DATABASE
        )
        cursor = conn.cursor()

        # Query segura com parâmetros (%s)
        query = """
        INSERT INTO dbo.Produtos (nome, descricao, preco, imagem_url)
        VALUES (%s, %s, %s, %s)
        """
        values = (name, description, price, image_url)
        cursor.execute(query, values)

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar no banco de dados: {e}")
        return False

def list_products():
    try:
        # Conexão com o banco de dados
        conn = pymssql.connect(
            server=SQL_SERVER,
            user=SQL_USER,
            password=SQL_PASSWORD,
            database=SQL_DATABASE
        )
        cursor = conn.cursor()

        # Query para listar produtos
        query = "SELECT nome, descricao, preco, imagem_url FROM dbo.Produtos"
        cursor.execute(query)
        products = cursor.fetchall()

        conn.close()
        return products
    except Exception as e:
        st.error(f"Erro ao listar produtos: {e}")
        return []

def list_products_screen():
    products = list_products()
    if products:
        cards_por_linha = 3
        for i, product in enumerate(products):
            # Recria as colunas a cada nova linha
            if i % cards_por_linha == 0:
                cols = st.columns(cards_por_linha)

            col = cols[i % cards_por_linha]
            with col:
                st.markdown(f"**Nome:** {product[0]}")
                st.write(f"**Descrição:** {product[1]}")
                st.write(f"**Preço:** R$ {product[2]:.2f}")
                if product[3]:
                    html_img = f'<img src="{product[3]}" alt="Imagem do Produto" style="width: 100%; height: auto;">'
                    st.markdown(html_img, unsafe_allow_html=True)
                st.markdown("---")
    else:
        st.write("Nenhum produto cadastrado.")
 


if st.button('Salvar Produto'):
    insert_product(product_name, product_price, product_description, product_image)
    return_message = "Produto salvo com sucesso!"
    list_products_screen()

st.header('Produtos Cadastrados')

if st.button('Listar Produtos'):
    list_products_screen()
    # Exibir mensagem de sucesso
    st.success("Produtos listados com sucesso!")
   