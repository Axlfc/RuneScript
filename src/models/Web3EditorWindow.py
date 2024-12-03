import os
import sys
import json
import logging
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from tkinter import scrolledtext
from web3 import Web3
import solcx
from solcx import compile_standard, install_solc
import tkinter.font as tkFont
import re

# Install Solidity compiler version
install_solc('0.8.19')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('web3_dev_studio.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Configuration Manager
class ConfigManager:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = {}
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except json.JSONDecodeError:
                logging.error("Invalid JSON in config file", exc_info=True)
                self.config = {}
        else:
            self.config = {}

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

# Wallet Manager
class WalletManager:
    def __init__(self):
        self.current_account = None

    def connect_wallet(self):
        private_key = simpledialog.askstring(
            "Private Key",
            "Enter your private key (will not be stored):",
            show='*'
        )
        if private_key:
            try:
                self.current_account = Web3().eth.account.privateKeyToAccount(private_key)
                messagebox.showinfo(
                    "Wallet Connected",
                    f"Connected to account {self.current_account.address}")
            except Exception as e:
                logging.error("Failed to connect wallet", exc_info=True)
                messagebox.showerror(
                    "Error",
                    f"Failed to connect wallet: {str(e)}")
        else:
            messagebox.showerror(
                "Error",
                "Private key is required to connect wallet")

# Code Editor with Advanced Features
class Editor(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack(fill=tk.BOTH, expand=True)
        self.create_widgets()
        self.bind_events()
        self.initialize_tags()

    def create_widgets(self):
        # Create a Frame for Line Numbers and Text Editor
        self.editor_frame = tk.Frame(self)
        self.editor_frame.pack(fill=tk.BOTH, expand=True)

        # Line Numbers
        self.line_numbers = tk.Text(
            self.editor_frame, width=4, padx=4, takefocus=0,
            border=0, background='#F0F0F0', state='disabled')
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Text Widget for Contract Editing
        self.text_widget = tk.Text(
            self.editor_frame, wrap=tk.NONE, undo=True)
        self.text_widget.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Scrollbar
        self.scrollbar = tk.Scrollbar(
            self.editor_frame, command=self.sync_scroll)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget.config(yscrollcommand=self.scrollbar.set)

    def bind_events(self):
        self.text_widget.bind("<KeyRelease>", self.on_key_release)
        self.text_widget.bind("<Return>", self.handle_auto_indent)
        self.text_widget.bind("<MouseWheel>", self.on_scroll_windows)
        self.text_widget.bind("<Button-4>", self.on_scroll_linux)
        self.text_widget.bind("<Button-5>", self.on_scroll_linux)

    def initialize_tags(self):
        italic_font = tkFont.Font(
            self.text_widget, self.text_widget.cget("font"))
        italic_font.configure(slant='italic')

        self.text_widget.tag_configure('keyword', foreground='#FF4500')
        self.text_widget.tag_configure('type', foreground='#2E8B57')
        self.text_widget.tag_configure('comment',
                                       foreground='#708090',
                                       font=italic_font)
        self.text_widget.tag_configure('string', foreground='#8B008B')
        self.text_widget.tag_configure('error',
                                       underline=True,
                                       foreground='red')

    def on_key_release(self, event):
        self.highlight_syntax()
        self.update_line_numbers()

    def on_scroll_windows(self, event):
        self.text_widget.yview_scroll(
            int(-1*(event.delta/120)), "units")
        self.line_numbers.yview_scroll(
            int(-1*(event.delta/120)), "units")
        return "break"

    def on_scroll_linux(self, event):
        if event.num == 4:
            self.text_widget.yview_scroll(-1, "units")
            self.line_numbers.yview_scroll(-1, "units")
        elif event.num == 5:
            self.text_widget.yview_scroll(1, "units")
            self.line_numbers.yview_scroll(1, "units")
        return "break"

    def sync_scroll(self, *args):
        self.text_widget.yview(*args)
        self.line_numbers.yview(*args)

    def handle_auto_indent(self, event):
        current_line = self.text_widget.index("insert").split('.')[0]
        previous_line = str(int(current_line) - 1)
        line_content = self.text_widget.get(
            f"{previous_line}.0", f"{previous_line}.end")
        indent = re.match(r'^(\s+)', line_content)
        indentation = indent.group(1) if indent else ''
        self.text_widget.insert("insert", f"\n{indentation}")
        return "break"

    def update_line_numbers(self):
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        line_count = int(self.text_widget.index('end-1c').split('.')[0])
        line_numbers_string = "\n".join(str(i) for i in range(1,
                                                              line_count))
        self.line_numbers.insert('1.0', line_numbers_string)
        self.line_numbers.config(state='disabled')

    def highlight_syntax(self):
        content = self.text_widget.get("1.0", tk.END)
        for tag in self.text_widget.tag_names():
            self.text_widget.tag_remove(tag, "1.0", tk.END)

        keyword_pattern = r'\b(contract|function|mapping|struct|pragma|' \
                          r'import|returns|event|modifier|public|private|' \
                          r'internal|external|view|pure|payable|constant|' \
                          r'if|else|for|while|do|break|continue|return|' \
                          r'new|delete|throw|emit|enum|require|assert|' \
                          r'revert|using|library|interface|storage|' \
                          r'memory|calldata|assembly|try|catch|fallback|' \
                          r'receive|abstract|override|virtual|immutable|' \
                          r'anonymous|indexed|constructor|type|this|' \
                          r'super)\b'
        type_pattern = r'\b(uint|int|address|string|bool|byte|bytes|' \
                       r'fixed|ufixed)\b'
        comment_pattern = r'(//.*?$|/\*.*?\*/)'
        string_pattern = r'".*?"'

        for match in re.finditer(keyword_pattern, content, re.MULTILINE):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add('keyword', start, end)

        for match in re.finditer(type_pattern, content, re.MULTILINE):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add('type', start, end)

        for match in re.finditer(comment_pattern,
                                 content,
                                 re.MULTILINE | re.DOTALL):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add('comment', start, end)

        for match in re.finditer(string_pattern, content, re.MULTILINE):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_widget.tag_add('string', start, end)

    def highlight_errors(self, error_lines):
        self.text_widget.tag_remove('error', '1.0', tk.END)
        for line_number in error_lines:
            line_start = f"{line_number}.0"
            line_end = f"{line_number}.end"
            self.text_widget.tag_add('error', line_start, line_end)

# Main Application Class
class Web3DevStudio:
    def __init__(self):
        self.root = tk.Toplevel()
        self.root.title("Web3 Development Studio")
        self.root.geometry("1280x800")

        # Initialize ConfigManager and WalletManager
        self.config_manager = ConfigManager()
        self.wallet_manager = WalletManager()

        # Ethereum Configuration
        self.network_configs = self.config_manager.get(
            'network_configs', {
                "Ethereum Mainnet": {
                    "rpc_url": "https://mainnet.infura.io/v3/YOUR-PROJECT-ID",
                    "chain_id": 1
                },
                "Sepolia Testnet": {
                    "rpc_url": "https://sepolia.infura.io/v3/YOUR-PROJECT-ID",
                    "chain_id": 11155111
                },
                "Goerli Testnet": {
                    "rpc_url": "https://goerli.infura.io/v3/YOUR-PROJECT-ID",
                    "chain_id": 5
                }
            })

        self.current_contract_path = None

        self.setup_ui()
        self.setup_project_structure()

    def setup_ui(self):
        # Main Layout Grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Sidebar
        self.sidebar = tk.Frame(self.root, width=200, bg="#2c3e50")
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Navigation Buttons
        nav_buttons = [
            ("📄 Contracts", self.show_contracts_view),
            ("🧪 Testing", self.show_testing_view),
            ("🚀 Deployment", self.show_deployment_view),
            ("⚙️ Settings", self.show_settings_view)
        ]

        for text, command in nav_buttons:
            btn = tk.Button(
                self.sidebar,
                text=text,
                command=command,
                bg="#34495e",
                fg="white",
                relief=tk.FLAT
            )
            btn.pack(fill=tk.X, padx=10, pady=5)

        # Main Workspace
        self.workspace = tk.Frame(self.root, bg="white")
        self.workspace.grid(row=0, column=1, sticky="nsew")

        # Bottom Console
        self.console = scrolledtext.ScrolledText(
            self.root,
            height=10,
            bg="#ecf0f1"
        )
        self.console.grid(row=1, column=0, columnspan=2, sticky="ew")

    def clear_workspace(self):
        """Clear all widgets from the workspace."""
        for widget in self.workspace.winfo_children():
            widget.destroy()

    def setup_project_structure(self):
        os.makedirs("contracts", exist_ok=True)
        os.makedirs("tests", exist_ok=True)
        os.makedirs("deployments", exist_ok=True)

    def show_contracts_view(self):
        self.clear_workspace()

        contract_frame = tk.Frame(self.workspace)
        contract_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        btn_frame = tk.Frame(contract_frame)
        btn_frame.pack(fill=tk.X)

        tk.Button(
            btn_frame, text="New Contract",
            command=self.create_new_contract
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            btn_frame, text="Open Contract",
            command=self.open_contract
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            btn_frame, text="Save Contract",
            command=self.save_contract
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            btn_frame, text="Save Contract As",
            command=self.save_contract_as
        ).pack(side=tk.LEFT, padx=5)

        # Integrate the advanced Editor
        self.editor = Editor(contract_frame)
        self.editor.pack(fill=tk.BOTH, expand=True)

    def create_new_contract(self):
        contract_name = simpledialog.askstring(
            "New Contract", "Enter Contract Name:")
        if contract_name:
            template = f"""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract {contract_name} {{
    // Your contract logic here

    constructor() {{
        // Initialization logic
    }}
}}"""
            self.editor.text_widget.delete('1.0', tk.END)
            self.editor.text_widget.insert(tk.END, template)
            self.current_contract_path = None

    def open_contract(self):
        file_path = filedialog.askopenfilename(
            initialdir="contracts",
            filetypes=[("Solidity Files", "*.sol")]
        )
        if file_path:
            with open(file_path, 'r') as file:
                content = file.read()
                self.editor.text_widget.delete('1.0', tk.END)
                self.editor.text_widget.insert(tk.END, content)
                self.current_contract_path = file_path

    def save_contract(self):
        if self.current_contract_path:
            content = self.editor.text_widget.get('1.0', tk.END)
            with open(self.current_contract_path, 'w') as file:
                file.write(content)
            messagebox.showinfo("Saved", "Contract saved successfully.")
        else:
            self.save_contract_as()

    def save_contract_as(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".sol",
            filetypes=[("Solidity Files", "*.sol")],
            initialdir="contracts"
        )
        if file_path:
            content = self.editor.text_widget.get('1.0', tk.END)
            with open(file_path, 'w') as file:
                file.write(content)
            self.current_contract_path = file_path
            messagebox.showinfo("Saved", "Contract saved successfully.")

    def show_testing_view(self):
        self.clear_workspace()

        testing_frame = tk.Frame(self.workspace)
        testing_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(testing_frame,
                 text="Select Testing Framework:").pack()
        test_frameworks = ["Hardhat", "Truffle", "Foundry"]
        self.test_framework_combo = ttk.Combobox(
            testing_frame, values=test_frameworks)
        self.test_framework_combo.pack()

        tk.Button(
            testing_frame,
            text="Run Tests",
            command=self.run_contract_tests
        ).pack(pady=10)

    def run_contract_tests(self):
        framework = self.test_framework_combo.get()
        if not framework:
            messagebox.showerror("Error", "Select a testing framework")
            return

        try:
            threading.Thread(target=self.execute_tests,
                             args=(framework,)).start()
        except Exception as e:
            logging.error(f"Test Execution Error: {e}")
            messagebox.showerror("Test Error", str(e))

    def execute_tests(self, framework):
        test_commands = {
            'Hardhat': ['npx', 'hardhat', 'test'],
            'Truffle': ['truffle', 'test'],
            'Foundry': ['forge', 'test']
        }

        command = test_commands.get(framework)
        if not command:
            messagebox.showerror(
                "Error", "Unsupported testing framework")
            return

        try:
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True)

            for line in iter(process.stdout.readline, ''):
                self.console.insert(tk.END, line)
                self.console.see(tk.END)

            process.stdout.close()
            process.wait()
        except Exception as e:
            logging.error("Test Execution Error", exc_info=True)
            messagebox.showerror("Test Error", str(e))

    def show_deployment_view(self):
        self.clear_workspace()

        deployment_frame = tk.Frame(self.workspace)
        deployment_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(deployment_frame, text="Select Network:").pack()
        networks = list(self.network_configs.keys())
        self.network_selector = ttk.Combobox(
            deployment_frame, values=networks)
        self.network_selector.pack()

        tk.Button(
            deployment_frame,
            text="Connect Wallet",
            command=self.wallet_manager.connect_wallet
        ).pack(pady=5)

        tk.Button(
            deployment_frame,
            text="Deploy Contract",
            command=self.deploy_contract
        ).pack(pady=10)

    def deploy_contract(self):
        network = self.network_selector.get()
        if not network:
            messagebox.showerror("Error", "Select a network")
            return

        try:
            compiled_sol = self.compile_contract()
            if not compiled_sol:
                return

            network_config = self.network_configs[network]
            w3 = Web3(Web3.HTTPProvider(network_config['rpc_url']))

            account = self.wallet_manager.current_account
            if not account:
                messagebox.showerror("Error", "No wallet connected")
                return

            w3.eth.default_account = account.address

            contract_key = list(compiled_sol['contracts'][
                'temp_contract.sol'].keys())[0]

            contract_interface = compiled_sol['contracts'][
                'temp_contract.sol'][contract_key]['abi']
            contract_bytecode = compiled_sol['contracts'][
                'temp_contract.sol'][contract_key]['evm'][
                    'bytecode']['object']

            contract = w3.eth.contract(
                abi=contract_interface, bytecode=contract_bytecode)

            tx = contract.constructor().buildTransaction({
                'from': account.address,
                'nonce': w3.eth.getTransactionCount(account.address),
                'gasPrice': w3.eth.gas_price,
                'chainId': network_config['chain_id']
            })

            signed_tx = account.sign_transaction(tx)
            tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

            messagebox.showinfo(
                "Deployment Successful",
                f"Contract deployed at {tx_receipt.contractAddress}"
            )
            self.console.insert(
                tk.END,
                f"Contract Deployed: {tx_receipt.contractAddress}\n"
            )
        except Exception as e:
            logging.error(f"Deployment Error: {e}")
            messagebox.showerror("Deployment Error", str(e))

    def compile_contract(self):
        contract_source_code = self.editor.text_widget.get("1.0", tk.END)

        # Use a unique temporary filename to avoid conflicts
        temp_filename = "temp_contract.sol"

        with open(temp_filename, "w") as f:
            f.write(contract_source_code)

        try:
            compiled_sol = compile_standard({
                "language": "Solidity",
                "sources": {
                    temp_filename: {
                        "content": contract_source_code
                    }
                },
                "settings": {
                    "outputSelection": {
                        "*": {
                            "*": ["abi", "evm.bytecode"]
                        }
                    }
                }
            }, solc_version="0.8.19")
            self.console.insert(tk.END, "Compilation Successful\n")
        except Exception as e:
            logging.error(f"Compilation Error: {e}")
            messagebox.showerror("Compilation Error", str(e))
            return None

        return compiled_sol

    def show_settings_view(self):
        self.clear_workspace()

        settings_frame = tk.Frame(self.workspace)
        settings_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(settings_frame, text="RPC Endpoints").pack()

        self.network_entries = {}

        for network, config in self.network_configs.items():
            frame = tk.Frame(settings_frame)
            frame.pack(fill=tk.X, padx=10, pady=5)

            tk.Label(frame, text=network).pack(side=tk.LEFT)
            entry = tk.Entry(frame, width=50)
            entry.insert(0, config['rpc_url'])
            entry.pack(side=tk.LEFT, padx=10)
            self.network_entries[network] = entry

        tk.Button(
            settings_frame,
            text="Save Settings",
            command=self.save_settings
        ).pack(pady=10)

    def save_settings(self):
        for network, entry in self.network_entries.items():
            rpc_url = entry.get()
            self.network_configs[network]['rpc_url'] = rpc_url

        self.config_manager.set('network_configs', self.network_configs)
        messagebox.showinfo("Settings Saved", "Network settings saved.")

def main():
    root = tk.Tk()
    app = Web3DevStudio(root)
    root.mainloop()

if __name__ == "__main__":
    main()
