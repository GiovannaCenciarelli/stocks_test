import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime
import sys
import os

class AnalisadorAcoes:
    def __init__(self, root):
        self.root = root
        self.root.title("Analisador de Ações Brasileiras v3.0")
        self.root.geometry("1100x750")
        self.root.configure(bg='#2c3e50')
        
        # Ações brasileiras mais negociadas (sem emojis nos códigos)
        self.acoes = {
            'PETR4.SA': 'Petrobras',
            'VALE3.SA': 'Vale',
            'ITUB4.SA': 'Itaú Unibanco',
            'BBDC4.SA': 'Bradesco',
            'B3SA3.SA': 'B3',
            'WEGE3.SA': 'Weg',
            'ABEV3.SA': 'Ambev',
            'BBAS3.SA': 'Banco do Brasil',
            'PETR3.SA': 'Petrobras PN'
        }
        
        self.dados_acoes = {}
        self.monitorando = False
        self.ultima_atualizacao = None
        
        self.criar_interface()
        self.verificar_conexao()
        
    def verificar_conexao(self):
        """Verifica se há conexão com internet"""
        try:
            # Usar método mais simples para verificar conexão
            yf.Ticker("PETR4.SA").history(period="1d", interval="1h")
            self.status_var.set("Conectado - Pronto para iniciar")
        except:
            self.status_var.set("Sem conexão - Verifique a internet")
        
    def criar_interface(self):
        """Cria a interface gráfica completa"""
        # Configurar estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Cabeçalho
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(header_frame, text="ANALISADOR DE ACÕES BRASILEIRAS", 
                 font=('Arial', 18, 'bold'), foreground='white', 
                 background='#2c3e50').pack()
        
        ttk.Label(header_frame, text="Monitoramento em Tempo Real", 
                 font=('Arial', 11), foreground='#bdc3c7', 
                 background='#2c3e50').pack()
        
        # Frame de controle
        control_frame = ttk.LabelFrame(main_frame, text="Controles", padding=15)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Botões principais
        btn_container = ttk.Frame(control_frame)
        btn_container.pack(fill=tk.X)
        
        self.btn_iniciar = ttk.Button(btn_container, text="INICIAR MONITORAMENTO", 
                                     command=self.iniciar_monitoramento)
        self.btn_iniciar.pack(side=tk.LEFT, padx=5)
        
        self.btn_parar = ttk.Button(btn_container, text="PARAR", 
                                   command=self.parar_monitoramento, state='disabled')
        self.btn_parar.pack(side=tk.LEFT, padx=5)
        
        self.btn_atualizar = ttk.Button(btn_container, text="ATUALIZAR AGORA", 
                                       command=self.atualizar_dados)
        self.btn_atualizar.pack(side=tk.LEFT, padx=5)
        
        # Configurações
        config_frame = ttk.Frame(control_frame)
        config_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.auto_update_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="Atualização automática a cada 2 minutos", 
                       variable=self.auto_update_var).pack(side=tk.LEFT)
        
        ttk.Label(config_frame, text="Intervalo:").pack(side=tk.LEFT, padx=(20, 5))
        
        self.intervalo_var = tk.StringVar(value="15m")
        intervalo_combo = ttk.Combobox(config_frame, textvariable=self.intervalo_var,
                                      values=["5m", "15m", "1h"], width=8, state="readonly")
        intervalo_combo.pack(side=tk.LEFT, padx=5)
        
        # Frame de cotações
        quotes_frame = ttk.LabelFrame(main_frame, text="Cotações em Tempo Real", padding=10)
        quotes_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Treeview para cotações
        columns = ('Ação', 'Último Preço (R$)', 'Variação %', 'Mínimo', 'Máximo', 'Volume', 'Atualização')
        self.tree = ttk.Treeview(quotes_frame, columns=columns, show='headings', height=8)
        
        # Configurar colunas
        col_widths = [180, 120, 100, 100, 100, 120, 120]
        for col, width in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor='center')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(quotes_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame do gráfico
        graph_frame = ttk.LabelFrame(main_frame, text="Gráfico de Preços", padding=10)
        graph_frame.pack(fill=tk.BOTH, expand=True)
        
        # Gráfico matplotlib
        self.fig, self.ax = plt.subplots(figsize=(12, 6), facecolor='#ecf0f1')
        self.canvas = FigureCanvasTkAgg(self.fig, graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar(value="Verificando conexão...")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief='sunken', style='TLabel')
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        # Texto inicial no gráfico
        self.mostrar_mensagem_inicial()
    
    def mostrar_mensagem_inicial(self):
        """Mostra mensagem inicial no gráfico"""
        self.ax.clear()
        self.ax.text(0.5, 0.5, 'Clique em "INICIAR MONITORAMENTO" para carregar os dados\n\n' +
                    'Obtendo cotações em tempo real\n' +
                    'Gráficos interativos\n' +
                    'Atualização automática', 
                    horizontalalignment='center', verticalalignment='center',
                    transform=self.ax.transAxes, fontsize=14, color='#7f8c8d',
                    linespacing=1.8)
        self.ax.set_facecolor('#ecf0f1')
        self.ax.set_title('Analisador de Ações Brasileiras', fontsize=16, 
                         fontweight='bold', pad=20, color='#2c3e50')
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw()
    
    def atualizar_status(self, mensagem):
        """Atualiza a barra de status"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.status_var.set(f"{timestamp} - {mensagem}")
        self.root.update_idletasks()
    
    def baixar_dados_simples(self, ticker):
        """Baixa dados de forma simples e robusta"""
        try:
            # Usar método Ticker que é mais estável
            acao = yf.Ticker(ticker)
            
            # Tentar diferentes períodos e intervalos
            intervalos_tentativa = [
                ("15m", "1d"),
                ("1h", "2d"),
                ("1d", "5d")
            ]
            
            for intervalo, periodo in intervalos_tentativa:
                try:
                    dados = acao.history(period=periodo, interval=intervalo)
                    if not dados.empty and len(dados) > 2:
                        return dados
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"Erro ao baixar {ticker}: {e}")
            return None
    
    def processar_dados_corrigido(self, dados, ticker):
        """Processa e limpa os dados de forma correta"""
        if dados is None or dados.empty:
            return None
            
        try:
            # Verificar se temos as colunas básicas
            if 'Close' not in dados.columns:
                return None
            
            # Garantir que o índice é datetime
            if not isinstance(dados.index, pd.DatetimeIndex):
                dados.index = pd.to_datetime(dados.index)
            
            # Ordenar por data
            dados = dados.sort_index()
            
            # Preencher valores faltantes para Close
            dados['Close'] = dados['Close'].ffill()
            
            # Se faltar outras colunas, criar com base no Close
            if 'Open' not in dados.columns:
                dados['Open'] = dados['Close']
            if 'High' not in dados.columns:
                dados['High'] = dados['Close']
            if 'Low' not in dados.columns:
                dados['Low'] = dados['Close']
            
            # Remover linhas com Close inválido
            dados = dados[dados['Close'] > 0]
            
            if len(dados) < 2:
                return None
                
            return dados.tail(50)  # Últimas 50 observações
            
        except Exception as e:
            print(f"Erro processando {ticker}: {e}")
            return None
    
    def formatar_volume(self, volume):
        """Formata volume para formato legível"""
        try:
            volume_val = float(volume)
            if volume_val >= 1_000_000_000:
                return f"{volume_val/1_000_000_000:.1f} Bi"
            elif volume_val >= 1_000_000:
                return f"{volume_val/1_000_000:.1f} Mi"
            elif volume_val >= 1_000:
                return f"{volume_val/1_000:.1f} Mil"
            else:
                return f"{volume_val:.0f}"
        except:
            return "N/A"
    
    def atualizar_tabela(self):
        """Atualiza a tabela de cotações"""
        # Limpar tabela
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Adicionar dados atualizados
        for ticker, nome in self.acoes.items():
            if ticker in self.dados_acoes and self.dados_acoes[ticker] is not None:
                dados = self.dados_acoes[ticker]
                if len(dados) > 1:
                    try:
                        ultimo = dados.iloc[-1]
                        preco_anterior = dados.iloc[-2]['Close'] if len(dados) > 1 else ultimo['Close']
                        
                        variacao = ((ultimo['Close'] - preco_anterior) / preco_anterior) * 100
                        hora_atualizacao = datetime.now().strftime('%H:%M:%S')
                        
                        # Obter mínimo e máximo do período disponível
                        minimo = dados['Low'].min() if 'Low' in dados.columns else ultimo['Close']
                        maximo = dados['High'].max() if 'High' in dados.columns else ultimo['Close']
                        volume = ultimo.get('Volume', 0)
                        
                        item_id = self.tree.insert('', 'end', values=(
                            f"{nome} ({ticker})",
                            f"R$ {ultimo['Close']:.2f}",
                            f"{variacao:+.2f}%",
                            f"R$ {minimo:.2f}",
                            f"R$ {maximo:.2f}",
                            self.formatar_volume(volume),
                            hora_atualizacao
                        ))
                        
                        # Colorir variação (usando texto simples)
                        if variacao < 0:
                            self.tree.set(item_id, 'Variação %', f"▼ {variacao:+.2f}%")
                        else:
                            self.tree.set(item_id, 'Variação %', f"▲ {variacao:+.2f}%")
                            
                    except Exception as e:
                        print(f"Erro ao adicionar {ticker} na tabela: {e}")
                        continue
    
    def atualizar_grafico(self):
        """Atualiza o gráfico com os dados mais recentes"""
        try:
            self.ax.clear()
            
            # Plotar cada ação que tem dados
            cores = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', 
                    '#1abc9c', '#d35400', '#c0392b', '#16a085']
            
            legend_labels = []
            legend_lines = []
            
            for i, (ticker, nome) in enumerate(self.acoes.items()):
                if ticker in self.dados_acoes and self.dados_acoes[ticker] is not None:
                    dados = self.dados_acoes[ticker]
                    if len(dados) > 5:
                        cor = cores[i % len(cores)]
                        line, = self.ax.plot(dados.index, dados['Close'], 
                                           color=cor, linewidth=2.5, alpha=0.8)
                        legend_labels.append(nome)
                        legend_lines.append(line)
            
            if legend_labels:
                self.ax.legend(legend_lines, legend_labels, bbox_to_anchor=(1.05, 1), loc='upper left')
            
            self.ax.set_title('Evolução dos Preços - Ações Brasileiras', 
                            fontsize=14, fontweight='bold', pad=20, color='#2c3e50')
            self.ax.set_ylabel('Preço (R$)', fontweight='bold', color='#2c3e50')
            self.ax.grid(True, alpha=0.3)
            self.ax.set_facecolor('#ecf0f1')
            
            # Formatar eixo x
            if len(legend_labels) > 0:
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M\n%d/%m'))
                self.fig.autofmt_xdate()
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"Erro ao atualizar gráfico: {e}")
            self.mostrar_mensagem_inicial()
    
    def atualizar_dados(self):
        """Atualiza dados em thread separada"""
        if self.monitorando:
            return
            
        def thread_atualizacao():
            self.monitorando = True
            self.root.after(0, lambda: self.btn_iniciar.config(state='disabled'))
            self.root.after(0, lambda: self.btn_parar.config(state='normal'))
            self.root.after(0, lambda: self.atualizar_status("Iniciando atualização de dados..."))
            
            try:
                for i, (ticker, nome) in enumerate(self.acoes.items()):
                    if not self.monitorando:
                        break
                    
                    self.root.after(0, lambda msg=f"Obtendo {nome}...": self.atualizar_status(msg))
                    
                    # Baixar e processar dados
                    dados_brutos = self.baixar_dados_simples(ticker)
                    dados_processados = self.processar_dados_corrigido(dados_brutos, ticker)
                    
                    if dados_processados is not None:
                        self.dados_acoes[ticker] = dados_processados
                    
                    time.sleep(0.5)  # Pausa menor entre requisições
                
                if self.monitorando:
                    self.ultima_atualizacao = datetime.now()
                    self.root.after(0, self.finalizar_atualizacao)
                    
            except Exception as e:
                self.root.after(0, lambda: self.atualizar_status(f"Erro na atualização: {str(e)}"))
        
        threading.Thread(target=thread_atualizacao, daemon=True).start()
    
    def finalizar_atualizacao(self):
        """Finaliza a atualização na thread principal"""
        self.atualizar_tabela()
        self.atualizar_grafico()
        
        tempo_decorrido = datetime.now().strftime('%H:%M:%S')
        self.atualizar_status(f"Dados atualizados com sucesso! ({tempo_decorrido})")
        
        # Reativar botão iniciar
        self.root.after(0, lambda: self.btn_iniciar.config(state='normal'))
        
        # Agendar próxima atualização se automática estiver ativada
        if self.auto_update_var.get() and self.monitorando:
            self.root.after(120000, self.atualizar_dados)  # 2 minutos
    
    def iniciar_monitoramento(self):
        """Inicia o monitoramento"""
        self.atualizar_dados()
    
    def parar_monitoramento(self):
        """Para o monitoramento"""
        self.monitorando = False
        self.btn_parar.config(state='disabled')
        self.btn_iniciar.config(state='normal')
        self.atualizar_status("Monitoramento parado")

def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas"""
    try:
        import yfinance
        import pandas
        import matplotlib
        return True
    except ImportError as e:
        print(f"Dependência faltando: {e}")
        return False

def main():
    """Função principal"""
    print("Iniciando Analisador de Ações Brasileiras...")
    
    if not verificar_dependencias():
        print("\nInstale as dependências com:")
        print("pip install yfinance pandas matplotlib")
        resposta = input("Deseja instalar automaticamente? (s/n): ")
        if resposta.lower() == 's':
            try:
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "pandas", "matplotlib"])
                print("Dependências instaladas com sucesso!")
            except:
                print("Erro ao instalar dependências. Instale manualmente.")
                return
        else:
            return
    
    # Criar aplicação
    root = tk.Tk()
    app = AnalisadorAcoes(root)
    
    # Centralizar janela
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # Configurar fechamento
    def on_closing():
        app.monitorando = False
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    try:
        root.mainloop()
    except Exception as e:
        print(f"Erro na aplicação: {e}")

if __name__ == "__main__":
    main()