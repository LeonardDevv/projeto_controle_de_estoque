import tkinter as tk
from tkinter import messagebox
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

# Função para conectar ao banco de dados SQLite
def conectar_db():
    conn = sqlite3.connect('mercadinho.db')
    return conn

# Função para criar a tabela se não existir
def criar_tabela():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            quantidade INTEGER NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            acao TEXT,
            quantidade_anterior INTEGER,
            quantidade_atual INTEGER,
            preco_anterior REAL,
            preco_atual REAL,
            data_movimentacao TEXT,
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    ''')
    conn.commit()
    conn.close()

# Função para carregar os produtos da tabela
def carregar_produtos():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produtos')
    produtos = cursor.fetchall()
    conn.close()
    return produtos

# Função para carregar o histórico do produto
def carregar_historico(produto_id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM historico WHERE produto_id = ?', (produto_id,))
    historico = cursor.fetchall()
    conn.close()
    return historico

# Função para formatar o texto com quebra de linha
def formatar_texto(texto, largura_max):
    palavras = texto.split()
    linhas = []
    linha_atual = ""
    for palavra in palavras:
        if len(linha_atual) + len(palavra) + 1 > largura_max:
            linhas.append(linha_atual)
            linha_atual = palavra
        else:
            if linha_atual:
                linha_atual += " "
            linha_atual += palavra
    linhas.append(linha_atual)
    return "\n".join(linhas)

# Função para atualizar a Listbox com os produtos
def atualizar_lista_produtos():
    lista_produtos.delete(0, tk.END)
    produtos = carregar_produtos()
    largura_max = 50
    for produto in produtos:
        texto_produto = f"ID: {produto[0]} | Nome: {produto[1]} | Preço: R$ {produto[2]:.2f} | Quantidade: {produto[3]}"
        texto_formatado = formatar_texto(texto_produto, largura_max)
        lista_produtos.insert(tk.END, texto_formatado)

# Função para adicionar um novo produto
def adicionar_produto():
    nome = entry_nome.get()
    preco = entry_preco.get()
    quantidade = entry_quantidade.get()

    if not nome or not preco or not quantidade:
        messagebox.showwarning("Aviso", "Todos os campos devem ser preenchidos!")
        return

    try:
        preco = float(preco)
        quantidade = int(quantidade)
    except ValueError:
        messagebox.showerror("Erro", "Preço deve ser um número e Quantidade deve ser um inteiro!")
        return

    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO produtos (nome, preco, quantidade) VALUES (?, ?, ?)', (nome, preco, quantidade))
    produto_id = cursor.lastrowid
    conn.commit()

    # Adiciona o histórico de criação
    adicionar_historico(produto_id, "Produto criado", 0, quantidade, preco, preco)

    conn.close()

    atualizar_lista_produtos()
    entry_nome.delete(0, tk.END)
    entry_preco.delete(0, tk.END)
    entry_quantidade.delete(0, tk.END)

# Função para remover um produto selecionado
def remover_produto():
    try:
        selecionado = lista_produtos.curselection()[0]
        produto_id = carregar_produtos()[selecionado][0]
    except IndexError:
        messagebox.showwarning("Aviso", "Nenhum produto selecionado!")
        return

    if messagebox.askyesno("Confirmação", "Você tem certeza que deseja remover este produto?"):
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM produtos WHERE id = ?', (produto_id,))
        conn.commit()
        conn.close()

        atualizar_lista_produtos()

# Função para atualizar o produto selecionado
def atualizar_produto():
    try:
        selecionado = lista_produtos.curselection()[0]
        produto_id = carregar_produtos()[selecionado][0]
    except IndexError:
        messagebox.showwarning("Aviso", "Nenhum produto selecionado!")
        return

    nome = entry_nome.get()
    preco = entry_preco.get()
    quantidade = entry_quantidade.get()

    if not nome or not preco or not quantidade:
        messagebox.showwarning("Aviso", "Todos os campos devem ser preenchidos!")
        return

    try:
        preco = float(preco)
        quantidade = int(quantidade)
    except ValueError:
        messagebox.showerror("Erro", "Preço deve ser um número e Quantidade deve ser um inteiro!")
        return

    # Recupera a quantidade e preço anterior
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT quantidade, preco FROM produtos WHERE id = ?', (produto_id,))
    resultado = cursor.fetchone()
    quantidade_anterior = resultado[0]
    preco_anterior = resultado[1]

    # Atualiza o produto no banco de dados
    cursor.execute('UPDATE produtos SET nome = ?, preco = ?, quantidade = ? WHERE id = ?', (nome, preco, quantidade, produto_id))
    conn.commit()

    # Adiciona ao histórico
    adicionar_historico(produto_id, "Produto atualizado", quantidade_anterior, quantidade, preco_anterior, preco)

    conn.close()

    atualizar_lista_produtos()
    entry_nome.delete(0, tk.END)
    entry_preco.delete(0, tk.END)
    entry_quantidade.delete(0, tk.END)

# Função para adicionar uma movimentação ao histórico
def adicionar_historico(produto_id, acao, quantidade_anterior, quantidade_atual, preco_anterior, preco_atual):
    data_movimentacao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO historico (produto_id, acao, quantidade_anterior, quantidade_atual, preco_anterior, preco_atual, data_movimentacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (produto_id, acao, quantidade_anterior, quantidade_atual, preco_anterior, preco_atual, data_movimentacao))
    conn.commit()
    conn.close()

# Função para exibir o histórico de um produto
def exibir_historico():
    try:
        selecionado = lista_produtos.curselection()[0]
        produto_id = carregar_produtos()[selecionado][0]
    except IndexError:
        messagebox.showwarning("Aviso", "Nenhum produto selecionado!")
        return

    historico = carregar_historico(produto_id)
    texto_historico = f"Histórico do Produto ID {produto_id}:\n"
    for entrada in historico:
        texto_historico += (f"{entrada[3]} -> {entrada[4]} (Preço: R$ {entrada[5]:.2f} -> R$ {entrada[6]:.2f}) em {entrada[7]}\n")

    messagebox.showinfo("Histórico", texto_historico)

# Função para gerar o relatório em Excel com gráfico
def gerar_relatorio():
    produtos = carregar_produtos()
    if not produtos:
        messagebox.showwarning("Aviso", "Nenhum produto disponível para gerar relatório.")
        return

    dados = {
        "Produto": [],
        "Quantidade Atual": [],
        "Quantidade Vendida": []
    }

    for produto in produtos:
        produto_id = produto[0]
        nome = produto[1]
        quantidade_atual = produto[3]

        # Simulação de quantidades vendidas para o relatório
        quantidade_vendida = max(0, 15 - quantidade_atual)  # Exemplo de cálculo de vendas

        dados["Produto"].append(nome)
        dados["Quantidade Atual"].append(quantidade_atual)
        dados["Quantidade Vendida"].append(quantidade_vendida)

    df = pd.DataFrame(dados)
    df.to_excel("relatorio_estoque.xlsx", index=False)

    # Gerar gráfico
    df.plot(x="Produto", y=["Quantidade Atual", "Quantidade Vendida"], kind="bar")
    plt.title("Relatório de Estoque")
    plt.ylabel("Quantidade")
    plt.savefig("relatorio_estoque.png")
    plt.show()

    messagebox.showinfo("Sucesso", "Relatório gerado com sucesso!")

# Função para abrir a janela de simulação de vendas
def abrir_janela_simular_venda():
    janela_venda = tk.Toplevel(root)
    janela_venda.title("Simular Venda")

    tk.Label(janela_venda, text="Número de vendas a simular:").pack(padx=10, pady=10)
    entry_vendas = tk.Entry(janela_venda)
    entry_vendas.pack(padx=10, pady=10)

    def confirmar_simulacao():
        try:
            quantidade_venda = int(entry_vendas.get())
            simular_venda(quantidade_venda)
            janela_venda.destroy()
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira um número válido.")

    tk.Button(janela_venda, text="Confirmar", command=confirmar_simulacao).pack(pady=10)

# Função para simular uma venda
def simular_venda(quantidade_venda):
    try:
        selecionado = lista_produtos.curselection()[0]
        produto_id = carregar_produtos()[selecionado][0]
    except IndexError:
        messagebox.showwarning("Aviso", "Nenhum produto selecionado!")
        return

    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT quantidade FROM produtos WHERE id = ?', (produto_id,))
    quantidade_atual = cursor.fetchone()[0]

    if quantidade_venda > quantidade_atual:
        messagebox.showwarning("Aviso", "Quantidade vendida é maior que a disponível!")
        return

    nova_quantidade = quantidade_atual - quantidade_venda
    cursor.execute('UPDATE produtos SET quantidade = ? WHERE id = ?', (nova_quantidade, produto_id))
    conn.commit()

    # Adiciona ao histórico
    adicionar_historico(produto_id, "Venda simulada", quantidade_atual, nova_quantidade, cursor.execute('SELECT preco FROM produtos WHERE id = ?', (produto_id,)).fetchone()[0], cursor.execute('SELECT preco FROM produtos WHERE id = ?', (produto_id,)).fetchone()[0])

    conn.close()

    atualizar_lista_produtos()
    messagebox.showinfo("Sucesso", "Venda simulada com sucesso!")

# Inicialização do banco de dados e criação da tabela
criar_tabela()

# Configuração da interface gráfica
root = tk.Tk()
root.title("Controle de Estoque")

# Frame para os controles
frame_controles = tk.Frame(root)
frame_controles.pack(pady=10)

# Entrada de Nome
tk.Label(frame_controles, text="Nome:").grid(row=0, column=0, padx=5, pady=5)
entry_nome = tk.Entry(frame_controles)
entry_nome.grid(row=0, column=1, padx=5, pady=5)

# Entrada de Preço
tk.Label(frame_controles, text="Preço:").grid(row=1, column=0, padx=5, pady=5)
entry_preco = tk.Entry(frame_controles)
entry_preco.grid(row=1, column=1, padx=5, pady=5)

# Entrada de Quantidade
tk.Label(frame_controles, text="Quantidade:").grid(row=2, column=0, padx=5, pady=5)
entry_quantidade = tk.Entry(frame_controles)
entry_quantidade.grid(row=2, column=1, padx=5, pady=5)

# Botão Adicionar
btn_adicionar = tk.Button(frame_controles, text="Adicionar", command=adicionar_produto)
btn_adicionar.grid(row=3, column=0, padx=5, pady=5)

# Botão Remover
btn_remover = tk.Button(frame_controles, text="Remover", command=remover_produto)
btn_remover.grid(row=3, column=1, padx=5, pady=5)

# Botão Atualizar
btn_atualizar = tk.Button(frame_controles, text="Atualizar", command=atualizar_produto)
btn_atualizar.grid(row=3, column=2, padx=5, pady=5)

# Botão Exibir Histórico
btn_historico = tk.Button(frame_controles, text="Exibir Histórico", command=exibir_historico)
btn_historico.grid(row=3, column=3, padx=5, pady=5)

# Botão Gerar Relatório
btn_relatorio = tk.Button(frame_controles, text="Gerar Relatório", command=gerar_relatorio)
btn_relatorio.grid(row=3, column=4, padx=5, pady=5)

# Botão Simular Venda
btn_simular_venda = tk.Button(frame_controles, text="Simular Venda", command=abrir_janela_simular_venda)
btn_simular_venda.grid(row=3, column=5, padx=5, pady=5)

# Listbox para exibir produtos
lista_produtos = tk.Listbox(root, width=70, height=15)  # Ajustado para maior largura
lista_produtos.pack(pady=10)

# Carregar produtos no início
atualizar_lista_produtos()

# Removido o preenchimento de itens iniciais

root.mainloop()
import tkinter as tk
from tkinter import messagebox
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

# Função para conectar ao banco de dados SQLite
def conectar_db():
    conn = sqlite3.connect('mercadinho.db')
    return conn

# Função para criar a tabela se não existir
def criar_tabela():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            quantidade INTEGER NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            acao TEXT,
            quantidade_anterior INTEGER,
            quantidade_atual INTEGER,
            preco_anterior REAL,
            preco_atual REAL,
            data_movimentacao TEXT,
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    ''')
    conn.commit()
    conn.close()

# Função para carregar os produtos da tabela
def carregar_produtos():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produtos')
    produtos = cursor.fetchall()
    conn.close()
    return produtos

# Função para carregar o histórico do produto
def carregar_historico(produto_id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM historico WHERE produto_id = ?', (produto_id,))
    historico = cursor.fetchall()
    conn.close()
    return historico

# Função para formatar o texto com quebra de linha
def formatar_texto(texto, largura_max):
    palavras = texto.split()
    linhas = []
    linha_atual = ""
    for palavra in palavras:
        if len(linha_atual) + len(palavra) + 1 > largura_max:
            linhas.append(linha_atual)
            linha_atual = palavra
        else:
            if linha_atual:
                linha_atual += " "
            linha_atual += palavra
    linhas.append(linha_atual)
    return "\n".join(linhas)

# Função para atualizar a Listbox com os produtos
def atualizar_lista_produtos():
    lista_produtos.delete(0, tk.END)
    produtos = carregar_produtos()
    largura_max = 50
    for produto in produtos:
        texto_produto = f"ID: {produto[0]} | Nome: {produto[1]} | Preço: R$ {produto[2]:.2f} | Quantidade: {produto[3]}"
        texto_formatado = formatar_texto(texto_produto, largura_max)
        lista_produtos.insert(tk.END, texto_formatado)

# Função para adicionar um novo produto
def adicionar_produto():
    nome = entry_nome.get()
    preco = entry_preco.get()
    quantidade = entry_quantidade.get()

    if not nome or not preco or not quantidade:
        messagebox.showwarning("Aviso", "Todos os campos devem ser preenchidos!")
        return

    try:
        preco = float(preco)
        quantidade = int(quantidade)
    except ValueError:
        messagebox.showerror("Erro", "Preço deve ser um número e Quantidade deve ser um inteiro!")
        return

    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO produtos (nome, preco, quantidade) VALUES (?, ?, ?)', (nome, preco, quantidade))
    produto_id = cursor.lastrowid
    conn.commit()

    # Adiciona o histórico de criação
    adicionar_historico(produto_id, "Produto criado", 0, quantidade, preco, preco)

    conn.close()

    atualizar_lista_produtos()
    entry_nome.delete(0, tk.END)
    entry_preco.delete(0, tk.END)
    entry_quantidade.delete(0, tk.END)

# Função para remover um produto selecionado
def remover_produto():
    try:
        selecionado = lista_produtos.curselection()[0]
        produto_id = carregar_produtos()[selecionado][0]
    except IndexError:
        messagebox.showwarning("Aviso", "Nenhum produto selecionado!")
        return

    if messagebox.askyesno("Confirmação", "Você tem certeza que deseja remover este produto?"):
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM produtos WHERE id = ?', (produto_id,))
        conn.commit()
        conn.close()

        atualizar_lista_produtos()

# Função para atualizar o produto selecionado
def atualizar_produto():
    try:
        selecionado = lista_produtos.curselection()[0]
        produto_id = carregar_produtos()[selecionado][0]
    except IndexError:
        messagebox.showwarning("Aviso", "Nenhum produto selecionado!")
        return

    nome = entry_nome.get()
    preco = entry_preco.get()
    quantidade = entry_quantidade.get()

    if not nome or not preco or not quantidade:
        messagebox.showwarning("Aviso", "Todos os campos devem ser preenchidos!")
        return

    try:
        preco = float(preco)
        quantidade = int(quantidade)
    except ValueError:
        messagebox.showerror("Erro", "Preço deve ser um número e Quantidade deve ser um inteiro!")
        return

    # Recupera a quantidade e preço anterior
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT quantidade, preco FROM produtos WHERE id = ?', (produto_id,))
    resultado = cursor.fetchone()
    quantidade_anterior = resultado[0]
    preco_anterior = resultado[1]

    # Atualiza o produto no banco de dados
    cursor.execute('UPDATE produtos SET nome = ?, preco = ?, quantidade = ? WHERE id = ?', (nome, preco, quantidade, produto_id))
    conn.commit()

    # Adiciona ao histórico
    adicionar_historico(produto_id, "Produto atualizado", quantidade_anterior, quantidade, preco_anterior, preco)

    conn.close()

    atualizar_lista_produtos()
    entry_nome.delete(0, tk.END)
    entry_preco.delete(0, tk.END)
    entry_quantidade.delete(0, tk.END)

# Função para adicionar uma movimentação ao histórico
def adicionar_historico(produto_id, acao, quantidade_anterior, quantidade_atual, preco_anterior, preco_atual):
    data_movimentacao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO historico (produto_id, acao, quantidade_anterior, quantidade_atual, preco_anterior, preco_atual, data_movimentacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (produto_id, acao, quantidade_anterior, quantidade_atual, preco_anterior, preco_atual, data_movimentacao))
    conn.commit()
    conn.close()

# Função para exibir o histórico de um produto
def exibir_historico():
    try:
        selecionado = lista_produtos.curselection()[0]
        produto_id = carregar_produtos()[selecionado][0]
    except IndexError:
        messagebox.showwarning("Aviso", "Nenhum produto selecionado!")
        return

    historico = carregar_historico(produto_id)
    texto_historico = f"Histórico do Produto ID {produto_id}:\n"
    for entrada in historico:
        texto_historico += (f"{entrada[3]} -> {entrada[4]} (Preço: R$ {entrada[5]:.2f} -> R$ {entrada[6]:.2f}) em {entrada[7]}\n")

    messagebox.showinfo("Histórico", texto_historico)

# Função para gerar o relatório em Excel com gráfico
def gerar_relatorio():
    produtos = carregar_produtos()
    if not produtos:
        messagebox.showwarning("Aviso", "Nenhum produto disponível para gerar relatório.")
        return

    dados = {
        "Produto": [],
        "Quantidade Atual": [],
        "Quantidade Vendida": []
    }

    for produto in produtos:
        produto_id = produto[0]
        nome = produto[1]
        quantidade_atual = produto[3]

        # Simulação de quantidades vendidas para o relatório
        quantidade_vendida = max(0, 15 - quantidade_atual)  # Exemplo de cálculo de vendas

        dados["Produto"].append(nome)
        dados["Quantidade Atual"].append(quantidade_atual)
        dados["Quantidade Vendida"].append(quantidade_vendida)

    df = pd.DataFrame(dados)
    df.to_excel("relatorio_estoque.xlsx", index=False)

    # Gerar gráfico
    df.plot(x="Produto", y=["Quantidade Atual", "Quantidade Vendida"], kind="bar")
    plt.title("Relatório de Estoque")
    plt.ylabel("Quantidade")
    plt.savefig("relatorio_estoque.png")
    plt.show()

    messagebox.showinfo("Sucesso", "Relatório gerado com sucesso!")

# Função para abrir a janela de simulação de vendas
def abrir_janela_simular_venda():
    janela_venda = tk.Toplevel(root)
    janela_venda.title("Simular Venda")

    tk.Label(janela_venda, text="Número de vendas a simular:").pack(padx=10, pady=10)
    entry_vendas = tk.Entry(janela_venda)
    entry_vendas.pack(padx=10, pady=10)

    def confirmar_simulacao():
        try:
            quantidade_venda = int(entry_vendas.get())
            simular_venda(quantidade_venda)
            janela_venda.destroy()
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira um número válido.")

    tk.Button(janela_venda, text="Confirmar", command=confirmar_simulacao).pack(pady=10)

# Função para simular uma venda
def simular_venda(quantidade_venda):
    try:
        selecionado = lista_produtos.curselection()[0]
        produto_id = carregar_produtos()[selecionado][0]
    except IndexError:
        messagebox.showwarning("Aviso", "Nenhum produto selecionado!")
        return

    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT quantidade FROM produtos WHERE id = ?', (produto_id,))
    quantidade_atual = cursor.fetchone()[0]

    if quantidade_venda > quantidade_atual:
        messagebox.showwarning("Aviso", "Quantidade vendida é maior que a disponível!")
        return

    nova_quantidade = quantidade_atual - quantidade_venda
    cursor.execute('UPDATE produtos SET quantidade = ? WHERE id = ?', (nova_quantidade, produto_id))
    conn.commit()

    # Adiciona ao histórico
    adicionar_historico(produto_id, "Venda simulada", quantidade_atual, nova_quantidade, cursor.execute('SELECT preco FROM produtos WHERE id = ?', (produto_id,)).fetchone()[0], cursor.execute('SELECT preco FROM produtos WHERE id = ?', (produto_id,)).fetchone()[0])

    conn.close()

    atualizar_lista_produtos()
    messagebox.showinfo("Sucesso", "Venda simulada com sucesso!")

# Inicialização do banco de dados e criação da tabela
criar_tabela()

# Configuração da interface gráfica
root = tk.Tk()
root.title("Controle de Estoque")

# Frame para os controles
frame_controles = tk.Frame(root)
frame_controles.pack(pady=10)

# Entrada de Nome
tk.Label(frame_controles, text="Nome:").grid(row=0, column=0, padx=5, pady=5)
entry_nome = tk.Entry(frame_controles)
entry_nome.grid(row=0, column=1, padx=5, pady=5)

# Entrada de Preço
tk.Label(frame_controles, text="Preço:").grid(row=1, column=0, padx=5, pady=5)
entry_preco = tk.Entry(frame_controles)
entry_preco.grid(row=1, column=1, padx=5, pady=5)

# Entrada de Quantidade
tk.Label(frame_controles, text="Quantidade:").grid(row=2, column=0, padx=5, pady=5)
entry_quantidade = tk.Entry(frame_controles)
entry_quantidade.grid(row=2, column=1, padx=5, pady=5)

# Botão Adicionar
btn_adicionar = tk.Button(frame_controles, text="Adicionar", command=adicionar_produto)
btn_adicionar.grid(row=3, column=0, padx=5, pady=5)

# Botão Remover
btn_remover = tk.Button(frame_controles, text="Remover", command=remover_produto)
btn_remover.grid(row=3, column=1, padx=5, pady=5)

# Botão Atualizar
btn_atualizar = tk.Button(frame_controles, text="Atualizar", command=atualizar_produto)
btn_atualizar.grid(row=3, column=2, padx=5, pady=5)

# Botão Exibir Histórico
btn_historico = tk.Button(frame_controles, text="Exibir Histórico", command=exibir_historico)
btn_historico.grid(row=3, column=3, padx=5, pady=5)

# Botão Gerar Relatório
btn_relatorio = tk.Button(frame_controles, text="Gerar Relatório", command=gerar_relatorio)
btn_relatorio.grid(row=3, column=4, padx=5, pady=5)

# Botão Simular Venda
btn_simular_venda = tk.Button(frame_controles, text="Simular Venda", command=abrir_janela_simular_venda)
btn_simular_venda.grid(row=3, column=5, padx=5, pady=5)

# Listbox para exibir produtos
lista_produtos = tk.Listbox(root, width=70, height=15)  # Ajustado para maior largura
lista_produtos.pack(pady=10)

# Carregar produtos no início
atualizar_lista_produtos()

# Removido o preenchimento de itens iniciais

root.mainloop()
