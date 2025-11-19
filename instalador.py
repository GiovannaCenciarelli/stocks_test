import subprocess
import sys
import tkinter as tk
from tkinter import messagebox
import os

def instalar_dependencias():
    """Instala dependências com interface gráfica"""
    root = tk.Tk()
    root.withdraw()  # Esconder janela principal
    
    try:
        # Lista de dependências
        dependencias = [
            "yfinance>=0.2.18",
            "pandas>=1.5.0",
            "matplotlib>=3.6.0"
        ]
        
        messagebox.showinfo("Instalador", "Iniciando instalação das dependências...")
        
        for dep in dependencias:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                print(f"✓ {dep} instalado")
            except subprocess.CalledProcessError:
                # Tentar sem versão específica
                dep_base = dep.split('>=')[0]
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep_base])
                print(f"✓ {dep_base} instalado")
        
        messagebox.showinfo("Sucesso", 
            "Instalação concluída!\n\n"
            "Agora você pode executar o programa com:\n"
            "python analisador_acoes.py\n\n"
            "Ou clique duplo no arquivo .py se o Python estiver configurado."
        )
        return True
        
    except Exception as e:
        messagebox.showerror("Erro", f"Falha na instalação: {e}")
        return False
    finally:
        root.destroy()

def criar_arquivo_execucao():
    """Cria um arquivo para facilitar a execução"""
    if sys.platform == "win32":
        # Criar arquivo .bat simples
        with open("EXECUTAR.bat", "w", encoding="utf-8") as f:
            f.write("""@echo off
chcp 65001 >nul
title Analisador de Ações
echo Executando Analisador de Ações Brasileiras...
python analisador_acoes.py
pause
""")
        print("Arquivo EXECUTAR.bat criado")

if __name__ == "__main__":
    print("=" * 60)
    print("INSTALADOR DO ANALISADOR DE AÇÕES BRASILEIRAS")
    print("=" * 60)
    
    # Verificar se o arquivo principal existe
    if not os.path.exists("analisador_acoes.py"):
        print("ERRO: Arquivo 'analisador_acoes.py' não encontrado!")
        print("Certifique-se de que todos os arquivos estão na mesma pasta.")
        input("Pressione Enter para sair...")
        sys.exit(1)
    
    # Instalar dependências
    if instalar_dependencias():
        criar_arquivo_execucao()
        print("\n✅ Instalação concluída com sucesso!")
    else:
        print("\n❌ Erro na instalação.")
    
    input("\nPressione Enter para finalizar...")