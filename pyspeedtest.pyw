"""
PY-SpeedTest - Modern UI
Fresh Design dengan Grey/Blue Ocean Theme
Same functionality as pyspeedtest.pyw dengan UI yang lebih modern

Nama: Ugi Sugiman Rahmatullah
NPM: 714240016
Kelas: D4 Teknik Informatika
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import threading
import csv
import os
import re
from datetime import datetime


# Matplotlib for charts
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt


# Import NetworkTester from original file
from pyspeedtest import NetworkTester

# RAG System imports
try:
    from supabase_manager import SupabaseManager
    from rag_manager import MistralRAGAnalyzer

    RAG_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ RAG system not available: {e}")
    RAG_AVAILABLE = False

# Set CustomTkinter appearance
ctk.set_appearance_mode("dark")

# ==================== COLOR THEME ====================
COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_card": "#16213e",
    "bg_card_light": "#1f3460",
    "primary": "#0f4c75",
    "primary_light": "#3282b8",
    "accent": "#00b4d8",
    "success": "#00ff88",
    "warning": "#ffc107",
    "danger": "#ff4757",
    "text": "#ffffff",
    "text_dim": "#a0aec0",
}

HISTORY_FILE = "speed_test_history.csv"

# ==================== MODERN UI APPLICATION ====================


class PyNetSpeedMonitorModern:
    """Modern UI Application dengan Grey/Blue Ocean Theme"""

    def __init__(self, root):
        self.root = root
        self.root.title("⚡ PY-SpeedTest")
        self.root.geometry("1300x850")
        self.root.configure(fg_color=COLORS["bg_dark"])

        # Network Tester
        self.tester = NetworkTester()
        self.is_testing = False

        # Test results
        self.test_results = {
            "ping": 0,
            "jitter": 0,
            "download": 0,
            "upload": 0,
            "timestamp": "",
            "server": "",
            "isp": "",
            "ip": "",
        }

        # RAG System
        self.supabase_manager = None
        self.rag_analyzer = None
        self.rag_enabled = False

        # Session ID
        import uuid

        self.session_id = str(uuid.uuid4())

        # UI References
        self.test_button = None
        self.result_cards_frame = None
        self.ping_label = None
        self.jitter_label = None
        self.download_label = None
        self.upload_label = None

        # Setup UI
        self.setup_ui()

        # Initialize
        self.initialize_network_info()
        self.load_charts_data()

        # Initialize RAG in background
        if RAG_AVAILABLE:
            threading.Thread(target=self.initialize_rag_system, daemon=True).start()

    def setup_ui(self):
        """Setup complete UI"""
        # Main container
        self.main_frame = ctk.CTkFrame(self.root, fg_color=COLORS["bg_dark"])
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # ===== HEADER =====
        self.create_header(self.main_frame)

        # ===== INFO CARDS (Server, ISP, IP) =====
        self.create_info_cards(self.main_frame)

        # ===== MAIN CONTENT (3 columns) =====
        content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, pady=(20, 0))

        content_frame.grid_columnconfigure(0, weight=1)  # Charts
        content_frame.grid_columnconfigure(1, weight=1)  # Test Control
        content_frame.grid_columnconfigure(2, weight=1)  # AI Summary

        # Left: Charts
        self.create_charts_section(content_frame)

        # Center: Test Control
        self.create_test_section(content_frame)

        # Right: AI Summary
        self.create_ai_summary_section(content_frame)

        # ===== OVERLAY CONTAINER (for modals) =====
        self.overlay_frame = None
        self.current_modal = None

    def create_header(self, parent):
        """Create header with title and buttons"""
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        # Title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left")

        title = ctk.CTkLabel(
            title_frame,
            text="⚡ PY-SpeedTest",
            font=("Segoe UI", 28, "bold"),
            text_color=COLORS["accent"],
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_frame,
            text="Network Quality of Service Tester • Socket Programming",
            font=("Segoe UI", 12),
            text_color=COLORS["text_dim"],
        )
        subtitle.pack(anchor="w")

        # Buttons
        buttons_frame = ctk.CTkFrame(header, fg_color="transparent")
        buttons_frame.pack(side="right")

        # View History Button
        history_btn = ctk.CTkButton(
            buttons_frame,
            text="📊 View History",
            font=("Segoe UI", 12, "bold"),
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["bg_card_light"],
            corner_radius=10,
            width=140,
            height=40,
            command=self.show_history,
        )
        history_btn.pack(side="left", padx=(0, 10))

        # Network Chat Button
        chat_btn = ctk.CTkButton(
            buttons_frame,
            text="💬 Network Chat",
            font=("Segoe UI", 12, "bold"),
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_light"],
            corner_radius=10,
            width=140,
            height=40,
            command=self.show_network_chatbot,
        )
        chat_btn.pack(side="left")

    def create_info_cards(self, parent):
        """Create Server, ISP, IP info cards"""
        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.pack(fill="x")

        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_columnconfigure(1, weight=1)
        info_frame.grid_columnconfigure(2, weight=1)

        # Server Card
        server_card = ctk.CTkFrame(
            info_frame, fg_color=COLORS["bg_card"], corner_radius=15
        )
        server_card.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(
            server_card,
            text="🌐 Server",
            font=("Segoe UI", 12),
            text_color=COLORS["text_dim"],
        ).pack(pady=(15, 5))

        self.server_label = ctk.CTkLabel(
            server_card,
            text="Detecting...",
            font=("Segoe UI", 14, "bold"),
            text_color=COLORS["accent"],
        )
        self.server_label.pack(pady=(0, 15))

        # ISP Card
        isp_card = ctk.CTkFrame(
            info_frame, fg_color=COLORS["bg_card"], corner_radius=15
        )
        isp_card.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(
            isp_card,
            text="📡 ISP",
            font=("Segoe UI", 12),
            text_color=COLORS["text_dim"],
        ).pack(pady=(15, 5))

        self.isp_label = ctk.CTkLabel(
            isp_card,
            text="Detecting...",
            font=("Segoe UI", 14, "bold"),
            text_color=COLORS["accent"],
        )
        self.isp_label.pack(pady=(0, 15))

        # IP Card
        ip_card = ctk.CTkFrame(info_frame, fg_color=COLORS["bg_card"], corner_radius=15)
        ip_card.grid(row=0, column=2, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(
            ip_card,
            text="🔒 IP Address",
            font=("Segoe UI", 12),
            text_color=COLORS["text_dim"],
        ).pack(pady=(15, 5))

        self.ip_label = ctk.CTkLabel(
            ip_card,
            text="Fetching...",
            font=("Segoe UI", 14, "bold"),
            text_color=COLORS["accent"],
        )
        self.ip_label.pack(pady=(0, 15))

    def create_charts_section(self, parent):
        """Create charts section with speed and latency charts"""
        charts_frame = ctk.CTkFrame(
            parent, fg_color=COLORS["bg_card"], corner_radius=15
        )
        charts_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Speed Chart Title
        ctk.CTkLabel(
            charts_frame,
            text="📈 Speed History",
            font=("Segoe UI", 14, "bold"),
            text_color=COLORS["text"],
        ).pack(pady=(15, 5), padx=15, anchor="w")

        # Speed Chart
        self.speed_fig = Figure(figsize=(4, 2.5), facecolor=COLORS["bg_card"])
        self.speed_ax = self.speed_fig.add_subplot(111)
        self.speed_ax.set_facecolor(COLORS["bg_dark"])
        self.style_chart(self.speed_ax)

        self.speed_canvas = FigureCanvasTkAgg(self.speed_fig, charts_frame)
        self.speed_canvas.get_tk_widget().pack(padx=15, pady=5, fill="x")

        # Latency Chart Title
        ctk.CTkLabel(
            charts_frame,
            text="📊 Latency History",
            font=("Segoe UI", 14, "bold"),
            text_color=COLORS["text"],
        ).pack(pady=(15, 5), padx=15, anchor="w")

        # Latency Chart
        self.latency_fig = Figure(figsize=(4, 2.5), facecolor=COLORS["bg_card"])
        self.latency_ax = self.latency_fig.add_subplot(111)
        self.latency_ax.set_facecolor(COLORS["bg_dark"])
        self.style_chart(self.latency_ax)

        self.latency_canvas = FigureCanvasTkAgg(self.latency_fig, charts_frame)
        self.latency_canvas.get_tk_widget().pack(padx=15, pady=(5, 15), fill="x")

    def style_chart(self, ax):
        """Apply consistent styling to chart axes"""
        ax.tick_params(colors=COLORS["text_dim"], labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(COLORS["text_dim"])
        ax.grid(True, alpha=0.2, color=COLORS["text_dim"])

    def create_test_section(self, parent):
        """Create test control section"""
        test_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=15)
        test_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Title
        ctk.CTkLabel(
            test_frame,
            text="🚀 Speed Test",
            font=("Segoe UI", 16, "bold"),
            text_color=COLORS["text"],
        ).pack(pady=(20, 10))

        # Container for result cards (always visible)
        self.test_container = ctk.CTkFrame(test_frame, fg_color="transparent")
        self.test_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Result cards frame (always visible)
        self.result_cards_frame = ctk.CTkFrame(
            self.test_container, fg_color="transparent"
        )
        self.result_cards_frame.pack(fill="both", expand=True)

        # Create result cards immediately (always visible)
        self.create_result_cards()

        # Start Test Button (below result cards, still inside test_container)
        self.test_button = ctk.CTkButton(
            self.test_container,
            text="🚀 START TESTING",
            font=("Segoe UI", 18, "bold"),
            fg_color=COLORS["accent"],
            hover_color=COLORS["primary_light"],
            text_color="black",
            corner_radius=15,
            height=50,
            command=self.start_test,
        )
        self.test_button.pack(fill="x", pady=(15, 5))

        # Progress section
        progress_frame = ctk.CTkFrame(test_frame, fg_color="transparent")
        progress_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.status_label = ctk.CTkLabel(
            progress_frame,
            text="Ready to test",
            font=("Segoe UI", 11),
            text_color=COLORS["text_dim"],
        )
        self.status_label.pack(pady=(10, 5))

        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            width=300,
            height=10,
            corner_radius=5,
            fg_color=COLORS["bg_dark"],
            progress_color=COLORS["accent"],
        )
        self.progress_bar.set(0)
        self.progress_bar.pack()

    def create_result_cards(self):
        """Create 4 result cards for ping, jitter, download, upload"""
        # Clear existing
        for widget in self.result_cards_frame.winfo_children():
            widget.destroy()

        self.result_cards_frame.grid_columnconfigure(0, weight=1)
        self.result_cards_frame.grid_columnconfigure(1, weight=1)

        # Ping Card
        ping_card = ctk.CTkFrame(
            self.result_cards_frame, fg_color=COLORS["bg_dark"], corner_radius=10
        )
        ping_card.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(
            ping_card,
            text="📡 Ping",
            font=("Segoe UI", 11),
            text_color=COLORS["text_dim"],
        ).pack(pady=(10, 2))
        self.ping_label = ctk.CTkLabel(
            ping_card,
            text="--",
            font=("Segoe UI", 24, "bold"),
            text_color=COLORS["success"],
        )
        self.ping_label.pack()
        ctk.CTkLabel(
            ping_card, text="ms", font=("Segoe UI", 10), text_color=COLORS["text_dim"]
        ).pack(pady=(0, 10))

        # Jitter Card
        jitter_card = ctk.CTkFrame(
            self.result_cards_frame, fg_color=COLORS["bg_dark"], corner_radius=10
        )
        jitter_card.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(
            jitter_card,
            text="📊 Jitter",
            font=("Segoe UI", 11),
            text_color=COLORS["text_dim"],
        ).pack(pady=(10, 2))
        self.jitter_label = ctk.CTkLabel(
            jitter_card,
            text="--",
            font=("Segoe UI", 24, "bold"),
            text_color=COLORS["primary_light"],
        )
        self.jitter_label.pack()
        ctk.CTkLabel(
            jitter_card, text="ms", font=("Segoe UI", 10), text_color=COLORS["text_dim"]
        ).pack(pady=(0, 10))

        # Download Card
        download_card = ctk.CTkFrame(
            self.result_cards_frame, fg_color=COLORS["bg_dark"], corner_radius=10
        )
        download_card.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(
            download_card,
            text="⬇️ Download",
            font=("Segoe UI", 11),
            text_color=COLORS["text_dim"],
        ).pack(pady=(10, 2))
        self.download_label = ctk.CTkLabel(
            download_card,
            text="--",
            font=("Segoe UI", 24, "bold"),
            text_color=COLORS["success"],
        )
        self.download_label.pack()
        ctk.CTkLabel(
            download_card,
            text="Mbps",
            font=("Segoe UI", 10),
            text_color=COLORS["text_dim"],
        ).pack(pady=(0, 10))

        # Upload Card
        upload_card = ctk.CTkFrame(
            self.result_cards_frame, fg_color=COLORS["bg_dark"], corner_radius=10
        )
        upload_card.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(
            upload_card,
            text="⬆️ Upload",
            font=("Segoe UI", 11),
            text_color=COLORS["text_dim"],
        ).pack(pady=(10, 2))
        self.upload_label = ctk.CTkLabel(
            upload_card,
            text="--",
            font=("Segoe UI", 24, "bold"),
            text_color=COLORS["warning"],
        )
        self.upload_label.pack()
        ctk.CTkLabel(
            upload_card,
            text="Mbps",
            font=("Segoe UI", 10),
            text_color=COLORS["text_dim"],
        ).pack(pady=(0, 10))

    def create_ai_summary_section(self, parent):
        """Create AI summary section"""
        ai_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=15)
        ai_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        # Title
        ctk.CTkLabel(
            ai_frame,
            text="🤖 AI Analysis",
            font=("Segoe UI", 14, "bold"),
            text_color=COLORS["text"],
        ).pack(pady=(15, 10), padx=15, anchor="w")

        # AI Summary Text
        self.ai_text = ctk.CTkTextbox(
            ai_frame,
            fg_color=COLORS["bg_dark"],
            corner_radius=10,
            font=("Segoe UI", 11),
            wrap="word",
        )
        self.ai_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Initial text
        self.ai_text.insert(
            "1.0",
            "AI analysis will appear here after running a speed test.\n\n• Run a test to get personalized insights\n• AI will analyze your network performance\n• Recommendations will be provided",
        )
        self.ai_text.configure(state="disabled")

    # ==================== FUNCTIONALITY ====================

    def initialize_network_info(self):
        """Initialize network info (server, ISP, IP)"""

        def fetch():
            self.tester.get_client_info()
            self.root.after(
                0,
                lambda: self.isp_label.configure(
                    text=(
                        self.tester.client_info["isp"][:25] + "..."
                        if len(self.tester.client_info["isp"]) > 25
                        else self.tester.client_info["isp"]
                    )
                ),
            )
            self.root.after(
                0, lambda: self.ip_label.configure(text=self.tester.client_info["ip"])
            )
            self.root.after(0, lambda: self.server_label.configure(text="Auto-select"))

        threading.Thread(target=fetch, daemon=True).start()

    def initialize_rag_system(self):
        """Initialize RAG system with hardcoded credentials"""
        try:
            # Hardcoded credentials
            mistral_key = "YOUR_API_KEY"
            supabase_url = "YOUR_SUPA_URL"
            supabase_key = "YOUR_SUPA_KEY"

            print("[RAG] Checking credentials...")
            print(f"   MISTRAL_API_KEY: {'Found' if mistral_key else 'Not found'}")
            print(f"   SUPABASE_URL: {'Found' if supabase_url else 'Not found'}")
            print(f"   SUPABASE_KEY: {'Found' if supabase_key else 'Not found'}")

            # Initialize Supabase
            if supabase_url and supabase_key:
                self.supabase_manager = SupabaseManager(supabase_url, supabase_key)
                if self.supabase_manager.connect():
                    print("[RAG] Connected to Supabase")
                else:
                    print(
                        "[RAG] Supabase connection failed - chat history won't be saved"
                    )
            else:
                print(
                    "[RAG] Supabase credentials not found - chat history won't be saved"
                )
                self.supabase_manager = None

            # Initialize RAG with Mistral
            self.rag_analyzer = MistralRAGAnalyzer(mistral_key, self.supabase_manager)
            self.rag_enabled = self.rag_analyzer.is_configured

            # Load chat history from Supabase
            self.chat_history = []
            self.conversation_memory = []

            if self.supabase_manager and self.supabase_manager.is_connected:
                try:
                    # Get IP first
                    user_ip = self.tester.client_info.get("ip", "unknown")
                    history = self.supabase_manager.get_user_chat_history(
                        user_ip, limit=10
                    )
                    self.chat_history = history if history else []
                    print(f"[RAG] Loaded {len(self.chat_history)} chat history items")
                except Exception as e:
                    print(f"[RAG] Could not load chat history: {e}")

            print(
                f"[RAG] System initialized (Mistral: {'Enabled' if self.rag_enabled else 'Disabled'})"
            )

        except Exception as e:
            print(f"[RAG] Init failed: {e}")
            import traceback

            traceback.print_exc()
            self.rag_enabled = False

    def load_charts_data(self):
        """Load history data and update charts"""
        try:
            if not os.path.exists(HISTORY_FILE):
                return

            history = []
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    history.append(row)

            if len(history) < 2:
                return

            # Get last 10 entries
            recent = history[-10:]

            times = [h["Timestamp"].split(" ")[1][:5] for h in recent]
            downloads = [float(h["Download"]) for h in recent]
            uploads = [float(h["Upload"]) for h in recent]
            pings = [float(h["Ping"]) for h in recent]
            jitters = [float(h["Jitter"]) for h in recent]

            # Speed Chart
            self.speed_ax.clear()
            self.speed_ax.set_facecolor(COLORS["bg_dark"])
            self.speed_ax.plot(
                times,
                downloads,
                color=COLORS["success"],
                linewidth=2,
                marker="o",
                markersize=4,
                label="Download",
            )
            self.speed_ax.plot(
                times,
                uploads,
                color=COLORS["warning"],
                linewidth=2,
                marker="o",
                markersize=4,
                label="Upload",
            )
            self.speed_ax.legend(
                fontsize=8, facecolor=COLORS["bg_card"], labelcolor=COLORS["text"]
            )
            self.speed_ax.set_ylabel("Mbps", color=COLORS["text_dim"], fontsize=8)
            self.style_chart(self.speed_ax)
            self.speed_fig.tight_layout()
            self.speed_canvas.draw()

            # Latency Chart
            self.latency_ax.clear()
            self.latency_ax.set_facecolor(COLORS["bg_dark"])
            self.latency_ax.plot(
                times,
                pings,
                color=COLORS["primary_light"],
                linewidth=2,
                marker="o",
                markersize=4,
                label="Ping",
            )
            self.latency_ax.plot(
                times,
                jitters,
                color=COLORS["danger"],
                linewidth=2,
                marker="o",
                markersize=4,
                label="Jitter",
            )
            self.latency_ax.legend(
                fontsize=8, facecolor=COLORS["bg_card"], labelcolor=COLORS["text"]
            )
            self.latency_ax.set_ylabel("ms", color=COLORS["text_dim"], fontsize=8)
            self.style_chart(self.latency_ax)
            self.latency_fig.tight_layout()
            self.latency_canvas.draw()

        except Exception as e:
            print(f"Error loading charts: {e}")

    def start_test(self):
        """Start speed test with animation"""
        if self.is_testing:
            return

        self.is_testing = True

        # Disable button during testing
        self.test_button.configure(
            state="disabled", text="⏳ Testing...", fg_color=COLORS["bg_card_light"]
        )

        # Reset values to show testing in progress
        self.ping_label.configure(text="--")
        self.jitter_label.configure(text="--")
        self.download_label.configure(text="--")
        self.upload_label.configure(text="--")
        self.progress_bar.set(0)

        def run_test():
            try:
                # Find best server
                self.update_status("🔍 Finding best server...", 0.1)
                best_server = self.tester.find_best_server()

                if best_server:
                    self.root.after(
                        0,
                        lambda: self.server_label.configure(
                            text=best_server["sponsor"]
                        ),
                    )

                # Test ping
                self.update_status("📡 Testing ping...", 0.2)
                avg_ping, latencies = self.tester.test_latency(
                    best_server["host"], best_server["port"]
                )
                jitter = self.tester.calculate_jitter(latencies)

                self.test_results["ping"] = avg_ping
                self.test_results["jitter"] = jitter
                self.root.after(
                    0, lambda: self.ping_label.configure(text=f"{int(avg_ping)}")
                )
                self.root.after(
                    0, lambda: self.jitter_label.configure(text=f"{int(jitter)}")
                )

                # Test download
                self.update_status("⬇️ Testing download...", 0.4)

                def dl_callback(msg, progress):
                    self.update_status(f"⬇️ {msg}", 0.4 + progress / 100 * 0.3)
                    speed = float(msg.split(":")[1].split()[0]) if ":" in msg else 0
                    self.root.after(
                        0,
                        lambda s=speed: self.download_label.configure(text=f"{s:.1f}"),
                    )

                download_speed = self.tester.test_download_speed(
                    duration=15, callback=dl_callback
                )
                self.test_results["download"] = download_speed
                self.root.after(
                    0,
                    lambda: self.download_label.configure(text=f"{download_speed:.2f}"),
                )

                # Test upload
                self.update_status("⬆️ Testing upload...", 0.7)

                def ul_callback(msg, progress):
                    self.update_status(f"⬆️ {msg}", 0.7 + progress / 100 * 0.25)

                upload_speed = self.tester.test_upload_speed_accurate(
                    callback=ul_callback
                )
                self.test_results["upload"] = upload_speed
                self.root.after(
                    0, lambda: self.upload_label.configure(text=f"{upload_speed:.2f}")
                )

                # Save results
                self.test_results["timestamp"] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                self.test_results["server"] = (
                    best_server["sponsor"] if best_server else "Unknown"
                )
                self.test_results["isp"] = self.tester.client_info["isp"]
                self.test_results["ip"] = self.tester.client_info["ip"]

                self.save_to_history()

                # Generate AI summary
                self.update_status("🤖 Generating AI analysis...", 0.95)
                self.generate_ai_summary()

                # Complete
                self.update_status("✅ Test complete!", 1.0)

                # Update charts
                self.root.after(100, self.load_charts_data)

            except Exception as e:
                self.update_status(f"❌ Error: {str(e)}", 0)
                print(f"Test error: {e}")

            finally:
                self.is_testing = False
                # Show button again after 3 seconds
                self.root.after(3000, self.reset_test_ui)

        threading.Thread(target=run_test, daemon=True).start()

    def update_status(self, message, progress):
        """Update status label and progress bar"""
        self.root.after(0, lambda: self.status_label.configure(text=message))
        self.root.after(0, lambda: self.progress_bar.set(progress))

    def reset_test_ui(self):
        """Reset test UI - re-enable button (cards stay visible with results)"""
        self.test_button.configure(
            state="normal", text="🚀 START TESTING", fg_color=COLORS["accent"]
        )

    def save_to_history(self):
        """Save test results to CSV and Supabase (for RAG)"""
        try:
            # 1. Save to local CSV
            file_exists = os.path.exists(HISTORY_FILE)
            with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(
                        [
                            "Timestamp",
                            "Server",
                            "ISP",
                            "IP",
                            "Ping",
                            "Jitter",
                            "Download",
                            "Upload",
                        ]
                    )
                writer.writerow(
                    [
                        self.test_results["timestamp"],
                        self.test_results["server"],
                        self.test_results["isp"],
                        self.test_results["ip"],
                        f"{self.test_results['ping']:.2f}",
                        f"{self.test_results['jitter']:.2f}",
                        f"{self.test_results['download']:.2f}",
                        f"{self.test_results['upload']:.2f}",
                    ]
                )
            print(f"✅ Results saved to {HISTORY_FILE}")

            # 2. Save to Supabase with embedding (for RAG)
            if self.rag_enabled and self.supabase_manager and self.rag_analyzer:
                try:
                    # Generate embedding for the test result
                    description = self.rag_analyzer.create_test_description(
                        self.test_results
                    )
                    embedding = self.rag_analyzer.generate_embedding(description)

                    # Save to Supabase speedtest_history table
                    if self.supabase_manager.save_test_result(
                        self.test_results, embedding
                    ):
                        print(
                            "✅ Saved to Supabase speedtest_history with embedding (for RAG)"
                        )
                    else:
                        print("⚠️ Failed to save to Supabase")
                except Exception as e:
                    print(f"⚠️ Could not save to Supabase: {e}")
            else:
                print("ℹ️ Supabase not enabled - results only saved locally")

        except Exception as e:
            print(f"Error saving history: {e}")

    def generate_ai_summary(self):
        """Generate AI summary using RAG - calls Mistral API"""
        try:
            if self.rag_enabled and self.rag_analyzer:
                # Use the generate_quick_summary method for natural response
                response = self.rag_analyzer.generate_quick_summary(self.test_results)
                formatted = self.format_response(response)
            else:
                # Fallback
                formatted = self.get_fallback_summary()

            self.root.after(0, lambda: self.update_ai_text(formatted))

        except Exception as e:
            print(f"AI summary error: {e}")
            import traceback

            traceback.print_exc()
            self.root.after(0, lambda: self.update_ai_text(self.get_fallback_summary()))

    def format_response(self, text):
        """Format response - remove raw markdown for cleaner display"""
        if not text:
            return ""

        # Remove markdown symbols
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # Bold **text**
        text = re.sub(r"\*(.+?)\*", r"\1", text)  # Italic *text*
        text = re.sub(r"__(.+?)__", r"\1", text)  # Bold __text__
        text = re.sub(r"_(.+?)_", r"\1", text)  # Italic _text_
        text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)  # Headers
        text = re.sub(r"^-\s*", "• ", text, flags=re.MULTILINE)  # Lists -
        text = re.sub(r"^\*\s+", "• ", text, flags=re.MULTILINE)  # Lists *
        text = re.sub(r"`(.+?)`", r"\1", text)  # Code `text`
        text = re.sub(r"\n{3,}", "\n\n", text)  # Multiple newlines

        return text.strip()

    def get_fallback_summary(self):
        """Get fallback AI summary"""
        dl = self.test_results["download"]
        ul = self.test_results["upload"]
        ping = self.test_results["ping"]
        jitter = self.test_results["jitter"]

        perf = "sangat baik" if dl > 50 else "baik" if dl > 25 else "cukup"

        return f"""✅ Test Selesai!

📊 Hasil Test:
• Download: {dl:.2f} Mbps
• Upload: {ul:.2f} Mbps
• Ping: {int(ping)} ms
• Jitter: {int(jitter)} ms

📈 Analisis:
Performa jaringan Anda {perf}. {'Cocok untuk streaming 4K dan gaming!' if dl > 50 else 'Cocok untuk streaming HD dan browsing.' if dl > 25 else 'Cocok untuk browsing dasar.'}

💡 Rekomendasi:
• {'Koneksi excellent untuk semua aktivitas online' if dl > 50 else 'Pertimbangkan upgrade untuk kualitas lebih baik' if dl < 25 else 'Bagus untuk work from home'}
• {'Latency rendah - bagus untuk gaming' if ping < 50 else 'Latency moderate - cukup untuk kebanyakan aktivitas' if ping < 100 else 'Latency tinggi - mungkin ada lag'}"""

    def update_ai_text(self, text):
        """Update AI summary textbox"""
        self.ai_text.configure(state="normal")
        self.ai_text.delete("1.0", "end")
        self.ai_text.insert("1.0", text)
        self.ai_text.configure(state="disabled")

    # ==================== OVERLAY MODAL SYSTEM ====================

    def create_overlay(self):
        """Create overlay backdrop for modals"""
        if self.overlay_frame is not None:
            return

        # Create semi-transparent overlay
        self.overlay_frame = ctk.CTkFrame(
            self.root, fg_color="#000000", corner_radius=0
        )
        self.overlay_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Make it semi-transparent by using a very dark color
        self.overlay_frame.configure(fg_color="#0a0a0a")

        # Click on overlay to close
        self.overlay_frame.bind("<Button-1>", lambda e: self.close_modal())

    def close_modal(self):
        """Close current modal and overlay"""
        if self.current_modal is not None:
            self.current_modal.destroy()
            self.current_modal = None

        if self.overlay_frame is not None:
            self.overlay_frame.destroy()
            self.overlay_frame = None

    # ==================== HISTORY MODAL ====================

    def show_history(self):
        """Show history modal as overlay"""
        # Close any existing modal
        self.close_modal()

        # Create overlay backdrop
        self.create_overlay()

        # Create modal container
        self.current_modal = ctk.CTkFrame(
            self.root,
            fg_color=COLORS["bg_dark"],
            corner_radius=20,
            border_width=2,
            border_color=COLORS["primary"],
        )
        self.current_modal.place(
            relx=0.5, rely=0.5, anchor="center", relwidth=0.85, relheight=0.8
        )

        # Header with close button
        header = ctk.CTkFrame(
            self.current_modal, fg_color=COLORS["primary"], corner_radius=15
        )
        header.pack(fill="x", padx=3, pady=(3, 0))

        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            header_content,
            text="📊 Speed Test History",
            font=("Segoe UI", 18, "bold"),
            text_color="white",
        ).pack(side="left")

        close_btn = ctk.CTkButton(
            header_content,
            text="✕",
            width=35,
            height=35,
            corner_radius=8,
            fg_color=COLORS["danger"],
            hover_color="#ff6b7a",
            font=("Segoe UI", 16, "bold"),
            command=self.close_modal,
        )
        close_btn.pack(side="right")

        # Content
        content = ctk.CTkScrollableFrame(
            self.current_modal, fg_color=COLORS["bg_card"], corner_radius=15
        )
        content.pack(fill="both", expand=True, padx=15, pady=15)

        # Load history
        try:
            if not os.path.exists(HISTORY_FILE):
                ctk.CTkLabel(
                    content,
                    text="No history yet",
                    text_color=COLORS["text_dim"],
                    font=("Segoe UI", 14),
                ).pack(pady=40)
                return

            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                history = list(reader)

            if not history:
                ctk.CTkLabel(
                    content,
                    text="No history yet",
                    text_color=COLORS["text_dim"],
                    font=("Segoe UI", 14),
                ).pack(pady=40)
                return

            # Headers
            headers_frame = ctk.CTkFrame(
                content, fg_color=COLORS["primary"], corner_radius=10
            )
            headers_frame.pack(fill="x", pady=(0, 10))

            headers_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

            for i, col in enumerate(["Time", "Server", "Ping", "Download", "Upload"]):
                ctk.CTkLabel(
                    headers_frame,
                    text=col,
                    font=("Segoe UI", 12, "bold"),
                    text_color="white",
                ).grid(row=0, column=i, padx=10, pady=12, sticky="ew")

            # Data rows (newest first)
            for idx, h in enumerate(reversed(history[-20:])):
                row_color = (
                    COLORS["bg_dark"] if idx % 2 == 0 else COLORS["bg_card_light"]
                )
                row_frame = ctk.CTkFrame(content, fg_color=row_color, corner_radius=8)
                row_frame.pack(fill="x", pady=2)

                row_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

                ctk.CTkLabel(
                    row_frame,
                    text=h["Timestamp"],
                    text_color=COLORS["text"],
                    font=("Segoe UI", 11),
                ).grid(row=0, column=0, padx=10, pady=8, sticky="ew")
                ctk.CTkLabel(
                    row_frame,
                    text=h["Server"][:20] + ("..." if len(h["Server"]) > 20 else ""),
                    text_color=COLORS["text"],
                    font=("Segoe UI", 11),
                ).grid(row=0, column=1, padx=10, pady=8, sticky="ew")
                ctk.CTkLabel(
                    row_frame,
                    text=f"{float(h['Ping']):.0f} ms",
                    text_color=COLORS["primary_light"],
                    font=("Segoe UI", 11, "bold"),
                ).grid(row=0, column=2, padx=10, pady=8, sticky="ew")
                ctk.CTkLabel(
                    row_frame,
                    text=f"{float(h['Download']):.2f} Mbps",
                    text_color=COLORS["success"],
                    font=("Segoe UI", 11, "bold"),
                ).grid(row=0, column=3, padx=10, pady=8, sticky="ew")
                ctk.CTkLabel(
                    row_frame,
                    text=f"{float(h['Upload']):.2f} Mbps",
                    text_color=COLORS["warning"],
                    font=("Segoe UI", 11, "bold"),
                ).grid(row=0, column=4, padx=10, pady=8, sticky="ew")

        except Exception as e:
            ctk.CTkLabel(
                content,
                text=f"Error: {e}",
                text_color=COLORS["danger"],
                font=("Segoe UI", 12),
            ).pack(pady=20)

    # ==================== NETWORK CHAT ====================

    def show_network_chatbot(self):
        """Show network chatbot as overlay modal"""
        # Close any existing modal
        self.close_modal()

        # Create overlay backdrop
        self.create_overlay()

        # Create modal container
        self.current_modal = ctk.CTkFrame(
            self.root,
            fg_color=COLORS["bg_dark"],
            corner_radius=20,
            border_width=2,
            border_color=COLORS["accent"],
        )
        self.current_modal.place(
            relx=0.5, rely=0.5, anchor="center", relwidth=0.45, relheight=0.85
        )

        # Header with close button
        header = ctk.CTkFrame(
            self.current_modal, fg_color=COLORS["primary"], corner_radius=15
        )
        header.pack(fill="x", padx=3, pady=(3, 0))

        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            header_content,
            text="💬 Network Assistant",
            font=("Segoe UI", 18, "bold"),
            text_color="white",
        ).pack(side="left")

        close_btn = ctk.CTkButton(
            header_content,
            text="✕",
            width=35,
            height=35,
            corner_radius=8,
            fg_color=COLORS["danger"],
            hover_color="#ff6b7a",
            font=("Segoe UI", 16, "bold"),
            command=self.close_modal,
        )
        close_btn.pack(side="right")

        # Chat messages
        self.chat_frame = ctk.CTkScrollableFrame(
            self.current_modal, fg_color=COLORS["bg_card"], corner_radius=15
        )
        self.chat_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Welcome message
        self.add_chat_message(
            "Halo! Saya Network Assistant.\nSilakan tanya apa saja tentang jaringan! 😊",
            is_bot=True,
        )

        # Input area
        input_frame = ctk.CTkFrame(self.current_modal, fg_color="transparent")
        input_frame.pack(fill="x", padx=15, pady=(0, 15))

        self.chat_input = ctk.CTkEntry(
            input_frame,
            placeholder_text="Tanya sesuatu...",
            height=45,
            corner_radius=12,
            fg_color=COLORS["bg_card"],
            font=("Segoe UI", 12),
        )
        self.chat_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.chat_input.bind("<Return>", lambda e: self.send_chat_message())

        send_btn = ctk.CTkButton(
            input_frame,
            text="Kirim",
            width=90,
            height=45,
            corner_radius=12,
            fg_color=COLORS["accent"],
            hover_color=COLORS["primary_light"],
            text_color="black",
            font=("Segoe UI", 12, "bold"),
            command=self.send_chat_message,
        )
        send_btn.pack(side="right")

        # Focus on input
        self.chat_input.focus()

    def add_chat_message(self, text, is_bot=False):
        """Add message to chat with icons"""
        # Outer container for vertical stacking
        msg_container = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        msg_container.pack(fill="x", pady=5, padx=10)

        if is_bot:
            # Bot message: Icon on left, bubble on right
            # Icon
            icon_label = ctk.CTkLabel(
                msg_container,
                text="🤖",
                font=("Segoe UI", 18),
                text_color=COLORS["text"],
            )
            icon_label.pack(side="left", padx=(0, 8))

            # Bubble
            msg_frame = ctk.CTkFrame(
                msg_container, fg_color=COLORS["bg_dark"], corner_radius=12
            )
            msg_frame.pack(side="left", anchor="w")

        else:
            # User message: Bubble on left, icon on right
            # Icon
            icon_label = ctk.CTkLabel(
                msg_container,
                text="👤",
                font=("Segoe UI", 18),
                text_color=COLORS["text"],
            )
            icon_label.pack(side="right", padx=(8, 0))

            # Bubble
            msg_frame = ctk.CTkFrame(
                msg_container, fg_color=COLORS["primary"], corner_radius=12
            )
            msg_frame.pack(side="right", anchor="e")

        # Message text
        ctk.CTkLabel(
            msg_frame,
            text=text,
            wraplength=200,
            justify="left",
            text_color=COLORS["text"],
            font=("Segoe UI", 11),
        ).pack(padx=14, pady=10)

    def send_chat_message(self):
        """Send chat message - uses Mistral AI for natural conversation"""
        message = self.chat_input.get().strip()
        if not message:
            return

        self.chat_input.delete(0, "end")
        self.add_chat_message(message, is_bot=False)

        # Show typing indicator
        self.add_chat_message("💭 Sedang mengetik...", is_bot=True)

        def get_response():
            try:
                response = ""

                if self.rag_enabled and self.rag_analyzer and self.rag_analyzer.client:
                    # Build context with current test results
                    current_test_context = f"""Hasil speed test saat ini (sesi ini):
- Download: {self.test_results['download']:.2f} Mbps
- Upload: {self.test_results['upload']:.2f} Mbps
- Ping: {self.test_results['ping']:.0f} ms
- Jitter: {self.test_results['jitter']:.0f} ms
- ISP: {self.test_results.get('isp', 'Unknown')}
- Server: {self.test_results.get('server', 'Unknown')}
- Timestamp: {self.test_results.get('timestamp', 'Belum test')}"""

                    # Get historical data from Supabase
                    history_context = ""
                    stats_context = ""

                    if self.supabase_manager and self.supabase_manager.is_connected:
                        try:
                            # Get recent tests (last 20)
                            recent_tests = self.supabase_manager.get_recent_tests(
                                limit=20
                            )

                            if recent_tests:
                                history_context = (
                                    "\n\nRiwayat Speed Test (20 test terakhir):\n"
                                )
                                for i, test in enumerate(
                                    recent_tests[:10]
                                ):  # Show first 10 in context
                                    history_context += (
                                        f"{i+1}. {test.get('timestamp', 'N/A')}: "
                                    )
                                    history_context += (
                                        f"DL={test.get('download_mbps', 0):.1f} Mbps, "
                                    )
                                    history_context += (
                                        f"UL={test.get('upload_mbps', 0):.1f} Mbps, "
                                    )
                                    history_context += (
                                        f"Ping={test.get('ping_ms', 0):.0f} ms\n"
                                    )

                                if len(recent_tests) > 10:
                                    history_context += f"... dan {len(recent_tests) - 10} test lainnya\n"

                                # Calculate statistics
                                downloads = [
                                    float(t.get("download_mbps", 0))
                                    for t in recent_tests
                                ]
                                uploads = [
                                    float(t.get("upload_mbps", 0)) for t in recent_tests
                                ]
                                pings = [
                                    float(t.get("ping_ms", 0)) for t in recent_tests
                                ]

                                if downloads:
                                    stats_context = f"""
Statistik dari {len(recent_tests)} test terakhir:
- Download: Min={min(downloads):.1f}, Max={max(downloads):.1f}, Rata-rata={sum(downloads)/len(downloads):.1f} Mbps
- Upload: Min={min(uploads):.1f}, Max={max(uploads):.1f}, Rata-rata={sum(uploads)/len(uploads):.1f} Mbps
- Ping: Min={min(pings):.0f}, Max={max(pings):.0f}, Rata-rata={sum(pings)/len(pings):.0f} ms"""
                            else:
                                history_context = (
                                    "\n\nBelum ada riwayat speed test di database."
                                )

                        except Exception as e:
                            print(f"Error fetching history: {e}")
                            history_context = (
                                "\n\n(Gagal mengambil riwayat dari database)"
                            )

                    # Combine all context
                    full_context = (
                        current_test_context + history_context + stats_context
                    )

                    # Build conversation history for memory
                    messages = [
                        {
                            "role": "system",
                            "content": f"""Kamu adalah Network Assistant, asisten AI yang ahli dalam jaringan internet dan teknologi. 
Kamu membantu user memahami hasil speed test dan masalah jaringan dengan bahasa Indonesia yang santai dan friendly.
Kamu MEMILIKI AKSES ke riwayat speed test user dari database.

{full_context}

Aturan:
1. Jawab dalam Bahasa Indonesia yang natural dan friendly
2. Berikan penjelasan yang mudah dipahami
3. Sertakan emoji untuk membuat percakapan lebih hidup
4. Jika ditanya tentang hasil test SAAT INI, gunakan data "Hasil speed test saat ini"
5. Jika ditanya tentang RIWAYAT atau HISTORY, gunakan data "Riwayat Speed Test" di atas
6. Jika ditanya tentang TREN atau STATISTIK, gunakan data statistik yang tersedia
7. Berikan saran praktis yang bisa langsung dilakukan
8. Jangan gunakan markdown formatting yang rumit
9. Jika user bertanya tentang 7 hari terakhir, bandingkan tanggal dari data riwayat""",
                        }
                    ]

                    # Add previous messages from this session (memory)
                    if hasattr(self, "conversation_memory"):
                        for mem in self.conversation_memory[-6:]:  # Last 6 messages
                            messages.append({"role": "user", "content": mem["user"]})
                            messages.append(
                                {"role": "assistant", "content": mem["bot"]}
                            )

                    # Add current message
                    messages.append({"role": "user", "content": message})

                    # Call Mistral API
                    chat_response = self.rag_analyzer.client.chat.complete(
                        model=self.rag_analyzer.generation_model, messages=messages
                    )

                    response = chat_response.choices[0].message.content
                    response = self.format_response(response)

                    # Save to memory
                    if not hasattr(self, "conversation_memory"):
                        self.conversation_memory = []
                    self.conversation_memory.append({"user": message, "bot": response})

                    # Save to Supabase
                    if self.supabase_manager and self.supabase_manager.is_connected:
                        try:
                            self.supabase_manager.save_chat_message(
                                user_ip=self.test_results.get("ip", "unknown"),
                                user_message=message,
                                bot_response=response,
                                session_id=self.session_id,
                                test_context=self.test_results,
                            )
                        except Exception as e:
                            print(f"Error saving chat: {e}")
                else:
                    response = self.get_simple_response(message)

                # Remove typing indicator and show response
                def update_ui():
                    # Remove last message (typing indicator)
                    children = self.chat_frame.winfo_children()
                    if children:
                        children[-1].destroy()
                    # Add response
                    self.add_chat_message(response, is_bot=True)

                self.root.after(0, update_ui)

            except Exception as e:
                print(f"Chat error: {e}")
                import traceback

                traceback.print_exc()

                def show_error():
                    children = self.chat_frame.winfo_children()
                    if children:
                        children[-1].destroy()
                    self.add_chat_message(
                        f"Maaf, terjadi error. Coba lagi ya! 😅\n({str(e)[:50]}...)",
                        is_bot=True,
                    )

                self.root.after(0, show_error)

        threading.Thread(target=get_response, daemon=True).start()

    def get_simple_response(self, message):
        """Simple fallback response when RAG is not available"""
        msg = message.lower()

        dl = self.test_results["download"]
        ul = self.test_results["upload"]
        ping = self.test_results["ping"]
        jitter = self.test_results["jitter"]

        if "ping" in msg or "latency" in msg:
            quality = (
                "sangat bagus! 🎮"
                if ping < 30
                else (
                    "bagus 👍"
                    if ping < 50
                    else "lumayan" if ping < 100 else "agak tinggi nih 😅"
                )
            )
            return f"""Ping kamu saat ini {ping:.0f} ms - {quality}

📊 Panduan Ping:
• < 30ms: Excellent (gaming, video call lancar)
• 30-50ms: Good (aktivitas umum OK)
• 50-100ms: Fair (browsing masih nyaman)
• > 100ms: Mungkin ada lag

💡 Tips: Coba restart router atau pindah lebih dekat ke WiFi untuk ping lebih rendah!"""

        elif "download" in msg:
            quality = (
                "super cepat! 🚀"
                if dl > 50
                else (
                    "cukup kencang 👍"
                    if dl > 25
                    else "standar" if dl > 10 else "agak lambat"
                )
            )
            return f"""Download speed kamu {dl:.2f} Mbps - {quality}

📊 Cocok untuk:
• Streaming 4K: butuh 25+ Mbps ({'✅ OK' if dl >= 25 else '❌ Kurang'})
• Gaming online: butuh 10+ Mbps ({'✅ OK' if dl >= 10 else '❌ Kurang'})
• Video call HD: butuh 5+ Mbps ({'✅ OK' if dl >= 5 else '❌ Kurang'})

💡 Kalau mau lebih cepat, coba pakai kabel LAN atau upgrade paket internet!"""

        elif "upload" in msg:
            quality = (
                "mantap! 🎥"
                if ul > 20
                else "bagus 👍" if ul > 10 else "cukup" if ul > 5 else "agak lambat"
            )
            return f"""Upload speed kamu {ul:.2f} Mbps - {quality}

📊 Cocok untuk:
• Live streaming: butuh 10+ Mbps ({'✅ OK' if ul >= 10 else '❌ Kurang'})
• Video call: butuh 3+ Mbps ({'✅ OK' if ul >= 3 else '❌ Kurang'})
• Upload file besar: {'Lumayan cepat!' if ul >= 10 else 'Mungkin butuh waktu'}

💡 Upload biasanya lebih lambat dari download, itu normal!"""

        elif "jitter" in msg:
            quality = (
                "stabil banget! 👌"
                if jitter < 10
                else "cukup stabil" if jitter < 30 else "agak goyang nih 😅"
            )
            return f"""Jitter kamu {jitter:.0f} ms - {quality}

Jitter = variasi ping. Makin rendah, makin stabil koneksi kamu.

📊 Panduan:
• < 10ms: Excellent (gaming & video call mantap)
• 10-30ms: Good (masih aman)
• > 30ms: Mungkin ada lag sesekali

💡 Jitter tinggi bisa bikin game/video call patah-patah. Coba restart router!"""

        elif "help" in msg or "bantuan" in msg:
            return (
                """Halo! Aku bisa bantu kamu soal:

📡 Ping & Latency - ketik "ping"
⬇️ Download Speed - ketik "download"  
⬆️ Upload Speed - ketik "upload"
📊 Jitter - ketik "jitter"
🔧 Tips koneksi - tanya apa saja!

Hasil test terakhir kamu:
• Ping: """
                + f"{ping:.0f} ms"
                + """
• Download: """
                + f"{dl:.2f} Mbps"
                + """
• Upload: """
                + f"{ul:.2f} Mbps"
                + """

Mau tanya apa? 😊"""
            )

        else:
            return f"""Hai! 👋 

Ini hasil speed test terakhir kamu:
📡 Ping: {ping:.0f} ms
⬇️ Download: {dl:.2f} Mbps
⬆️ Upload: {ul:.2f} Mbps
📊 Jitter: {jitter:.0f} ms

Secara keseluruhan, koneksi kamu {'bagus banget! 🚀' if dl > 50 and ping < 50 else 'cukup oke! 👍' if dl > 25 else 'standar.'} 

Mau tahu lebih detail? Tanya aku soal:
• ping / latency
• download speed
• upload speed
• jitter

Atau tanya apa saja tentang jaringan! 😊"""


# ==================== MAIN ====================

if __name__ == "__main__":
    root = ctk.CTk()
    app = PyNetSpeedMonitorModern(root)
    root.mainloop()
