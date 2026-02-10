"""
Mistral AI RAG Analyzer
Manages Mistral AI API integration and RAG operations for speedtest analysis
"""

from mistralai import Mistral
from typing import List, Dict, Optional
import time


class MistralRAGAnalyzer:
    """Manages Mistral AI API and RAG operations"""

    def __init__(self, api_key: str, supabase_manager=None):
        """
        Initialize Mistral AI client

        Args:
            api_key: Mistral AI API key
            supabase_manager: SupabaseManager instance for data retrieval
        """
        self.api_key = api_key
        self.supabase_manager = supabase_manager
        self.is_configured = False

        # Configure Mistral AI
        try:
            self.client = Mistral(api_key=api_key)
            self.embedding_model = "mistral-embed"  # Mistral embedding model
            self.generation_model = "mistral-large-latest"  # Mistral chat model
            self.is_configured = True
            print("✅ Mistral AI API configured")
        except Exception as e:
            print(f"❌ Mistral AI configuration error: {e}")
            self.is_configured = False

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding using Mistral AI embedding model

        Args:
            text: Text to embed

        Returns:
            List of floats (1024 dimensions for Mistral) or None if error
        """
        if not self.is_configured:
            print("❌ Mistral AI not configured")
            return None

        try:
            response = self.client.embeddings.create(
                model=self.embedding_model, inputs=[text]
            )
            return response.data[0].embedding

        except Exception as e:
            print(f"❌ Embedding generation error: {e}")
            return None

    def create_test_description(self, test_data: Dict) -> str:
        """
        Convert test data to text for embedding

        Args:
            test_data: Test result dictionary

        Returns:
            Formatted text description
        """
        # Assess network quality
        ping = float(test_data.get("ping", 0))
        jitter = float(test_data.get("jitter", 0))
        download = float(test_data.get("download", 0))
        upload = float(test_data.get("upload", 0))

        quality = self._assess_quality(ping, jitter, download, upload)

        return f"""Network Speed Test Results:
- Date: {test_data.get('timestamp', 'Unknown')}
- ISP: {test_data.get('isp', 'Unknown')}
- Server: {test_data.get('server', 'Unknown')}
- Latency: {ping}ms (Jitter: {jitter}ms)
- Download Speed: {download} Mbps
- Upload Speed: {upload} Mbps
- Network Quality: {quality}"""

    def _assess_quality(
        self, ping: float, jitter: float, download: float, upload: float
    ) -> str:
        """Assess network quality based on metrics"""
        if ping < 20 and jitter < 5 and download > 50 and upload > 20:
            return "Excellent"
        elif ping < 50 and jitter < 10 and download > 25 and upload > 10:
            return "Good"
        elif ping < 100 and jitter < 20 and download > 10 and upload > 5:
            return "Fair"
        else:
            return "Poor"

    def create_chat_embedding(
        self, user_message: str, bot_response: str
    ) -> Optional[List[float]]:
        """
        Create embedding for chat conversation

        Args:
            user_message: User's question
            bot_response: Bot's answer

        Returns:
            List of floats (1024 dimensions) or None if error
        """
        if not self.is_configured:
            print("❌ Mistral AI not configured")
            return None

        try:
            # Combine user message and bot response for context
            combined_text = f"""User Question: {user_message}
Bot Answer: {bot_response}"""

            # Generate embedding
            return self.generate_embedding(combined_text)

        except Exception as e:
            print(f"❌ Chat embedding generation error: {e}")
            return None

    def analyze_test_results(self, current_test: Dict) -> Dict:
        """
        Main RAG analysis function

        Args:
            current_test: Current test result dictionary

        Returns:
            Dictionary with analysis results
        """
        if not self.is_configured:
            return {"error": "Mistral AI API not configured", "success": False}

        try:
            # 1. Generate embedding for current test
            print("🔄 Generating embedding for current test...")
            test_description = self.create_test_description(current_test)
            embedding = self.generate_embedding(test_description)

            if not embedding:
                return {"error": "Failed to generate embedding", "success": False}

            # 2. Query similar historical tests
            print("🔄 Searching for similar historical tests...")
            similar_tests = []
            if self.supabase_manager and self.supabase_manager.is_connected:
                similar_tests = self.supabase_manager.query_similar_tests(
                    embedding, limit=5
                )

            # 3. Get statistics
            print("🔄 Calculating statistics...")
            stats = {}
            if self.supabase_manager and self.supabase_manager.is_connected:
                stats = self.supabase_manager.get_statistics()

            # 4. Build prompt and get AI analysis
            print("🔄 Generating AI analysis...")
            prompt = self.build_analysis_prompt(current_test, similar_tests, stats)

            # Use Mistral chat completion
            chat_response = self.client.chat.complete(
                model=self.generation_model,
                messages=[{"role": "user", "content": prompt}],
            )
            analysis_text = chat_response.choices[0].message.content

            # 5. Parse and structure response
            parsed_analysis = self.parse_ai_response(analysis_text)

            return {
                "success": True,
                "current_test": current_test,
                "similar_tests": similar_tests,
                "statistics": stats,
                "analysis": parsed_analysis,
                "raw_analysis": analysis_text,
            }

        except Exception as e:
            print(f"❌ Analysis error: {e}")
            return {"error": str(e), "success": False}

    def build_analysis_prompt(
        self, current_test: Dict, similar_tests: List[Dict], stats: Dict
    ) -> str:
        """
        Build comprehensive prompt with context

        Args:
            current_test: Current test data
            similar_tests: List of similar historical tests
            stats: Statistical data

        Returns:
            Formatted prompt string
        """
        # Format current test
        current_info = f"""
CURRENT TEST RESULTS:
- Timestamp: {current_test.get('timestamp', 'Unknown')}
- ISP: {current_test.get('isp', 'Unknown')}
- Server: {current_test.get('server', 'Unknown')}
- Ping: {current_test.get('ping', 0)}ms
- Jitter: {current_test.get('jitter', 0)}ms
- Download: {current_test.get('download', 0)} Mbps
- Upload: {current_test.get('upload', 0)} Mbps
"""

        # Format similar tests
        similar_info = "\nSIMILAR HISTORICAL TESTS:\n"
        if similar_tests:
            for i, test in enumerate(similar_tests[:5], 1):
                similar_info += f"""
Test {i}:
- Date: {test.get('timestamp', 'Unknown')}
- ISP: {test.get('isp', 'Unknown')}
- Server: {test.get('server_name', 'Unknown')}
- Ping: {test.get('ping_ms', 0)}ms, Jitter: {test.get('jitter_ms', 0)}ms
- Download: {test.get('download_mbps', 0)} Mbps, Upload: {test.get('upload_mbps', 0)} Mbps
"""
        else:
            similar_info += "No historical data available yet.\n"

        # Format statistics
        stats_info = "\nSTATISTICAL CONTEXT:\n"
        if stats and stats.get("count", 0) > 0:
            stats_info += f"""
- Total Tests: {stats.get('count', 0)}
- Average Ping: {stats.get('avg_ping', 0):.1f}ms
- Average Jitter: {stats.get('avg_jitter', 0):.1f}ms
- Average Download: {stats.get('avg_download', 0):.2f} Mbps
- Average Upload: {stats.get('avg_upload', 0):.2f} Mbps
- Best Download: {stats.get('max_download', 0):.2f} Mbps
- Best Upload: {stats.get('max_upload', 0):.2f} Mbps
- Best Ping: {stats.get('min_ping', 0):.1f}ms
"""
        else:
            stats_info += "No historical statistics available yet.\n"

        # Build complete prompt in Indonesian
        prompt = f"""Kamu adalah seorang ahli analisis performa jaringan internet. Analisis hasil speedtest berikut dan berikan insight yang mudah dipahami dalam Bahasa Indonesia.

{current_info}
{similar_info}
{stats_info}

Berikan analisis yang komprehensif dengan gaya bahasa yang santai dan mudah dipahami, seperti sedang berbicara dengan teman. Gunakan format berikut:

1. **Penilaian Performa**: Beri rating kualitas internet saat ini (Sangat Bagus/Bagus/Cukup/Kurang Bagus) dan jelaskan alasannya dengan bahasa yang mudah dimengerti.

2. **Analisis Tren**: Bandingkan hasil sekarang dengan data historis. Apakah internet makin cepat, makin lambat, atau stabil? Jelaskan dengan contoh konkret.

3. **Deteksi Anomali**: Cari pola yang tidak biasa atau aneh dari hasil test ini dibanding biasanya. Misalnya ping tiba-tiba tinggi atau download speed turun drastis.

4. **Analisis Penyebab**: Berdasarkan data yang ada, jelaskan kemungkinan penyebab performa saat ini. Contoh: "Sepertinya jaringan lagi rame nih" atau "Koneksi ke server jauh jadi ping-nya tinggi".

5. **Rekomendasi**: Berikan 3-5 saran praktis yang bisa langsung dilakukan untuk meningkatkan kualitas internet. Gunakan bahasa sehari-hari yang gampang dipahami.

Penting: Gunakan bahasa Indonesia yang natural, santai, dan mudah dipahami. Hindari istilah teknis yang terlalu rumit. Jika harus pakai istilah teknis, jelaskan artinya dengan bahasa sederhana."""

        return prompt

    def parse_ai_response(self, response: str) -> Dict:
        """
        Parse and structure AI response (supports Indonesian)

        Args:
            response: Raw AI response text

        Returns:
            Structured dictionary with sections
        """
        sections = {
            "performance_assessment": "",
            "trend_analysis": "",
            "anomaly_detection": "",
            "root_cause_analysis": "",
            "recommendations": [],
        }

        try:
            # Simple parsing - split by section headers (English & Indonesian)
            current_section = None
            lines = response.split("\n")

            for line in lines:
                line_lower = line.lower().strip()

                # Detect section headers (Indonesian & English)
                if (
                    "penilaian performa" in line_lower
                    or "performance assessment" in line_lower
                ):
                    current_section = "performance_assessment"
                elif "analisis tren" in line_lower or "trend analysis" in line_lower:
                    current_section = "trend_analysis"
                elif (
                    "deteksi anomali" in line_lower or "anomaly detection" in line_lower
                ):
                    current_section = "anomaly_detection"
                elif "analisis penyebab" in line_lower or "root cause" in line_lower:
                    current_section = "root_cause_analysis"
                elif "rekomendasi" in line_lower or "recommendation" in line_lower:
                    current_section = "recommendations"
                elif current_section and line.strip():
                    # Add content to current section
                    if current_section == "recommendations":
                        # Extract bullet points
                        if line.strip().startswith(
                            ("-", "•", "*", "1.", "2.", "3.", "4.", "5.")
                        ):
                            sections["recommendations"].append(line.strip())
                    else:
                        sections[current_section] += line + "\n"

            # Clean up sections
            for key in sections:
                if isinstance(sections[key], str):
                    sections[key] = sections[key].strip()

        except Exception as e:
            print(f"⚠️ Error parsing AI response: {e}")

        return sections

    def generate_summary(self, test_data: Dict) -> str:
        """
        Generate a quick summary without full RAG analysis

        Args:
            test_data: Test result dictionary

        Returns:
            Summary text
        """
        if not self.is_configured:
            return "Mistral AI API not configured"

        try:
            prompt = f"""Provide a brief 2-3 sentence summary of this network speed test:

Ping: {test_data.get('ping', 0)}ms
Jitter: {test_data.get('jitter', 0)}ms
Download: {test_data.get('download', 0)} Mbps
Upload: {test_data.get('upload', 0)} Mbps
ISP: {test_data.get('isp', 'Unknown')}

Focus on overall quality and any notable issues."""

            chat_response = self.client.chat.complete(
                model=self.generation_model,
                messages=[{"role": "user", "content": prompt}],
            )
            return chat_response.choices[0].message.content

        except Exception as e:
            print(f"❌ Summary generation error: {e}")
            return "Error generating summary"

    def generate_quick_summary(self, test_data: Dict) -> str:
        """
        Generate ringkasan singkat 1 paragraf untuk ditampilkan inline

        Args:
            test_data: Test result dictionary

        Returns:
            Summary text (1 paragraph, Indonesian, casual)
        """
        if not self.is_configured:
            return "Mistral AI belum dikonfigurasi. Silakan atur API key di Settings."

        try:
            # Assess quality
            ping = float(test_data.get("ping", 0))
            download = float(test_data.get("download", 0))
            upload = float(test_data.get("upload", 0))
            quality = self._assess_quality(
                ping, test_data.get("jitter", 0), download, upload
            )

            prompt = f"""Buat ringkasan singkat dalam 1 paragraf (maksimal 3-4 kalimat) tentang hasil speedtest ini. Gunakan bahasa Indonesia yang santai dan mudah dipahami:

Ping: {ping}ms
Download: {download} Mbps
Upload: {upload} Mbps
ISP: {test_data.get('isp', 'Unknown')}
Kualitas: {quality}

Fokus pada:
1. Penilaian kualitas secara keseluruhan
2. Cocok untuk aktivitas apa (streaming, gaming, video call, dll)
3. Satu insight atau saran singkat

Gunakan bahasa yang friendly dan to-the-point. Jangan pakai bullet points, cukup paragraf mengalir."""

            chat_response = self.client.chat.complete(
                model=self.generation_model,
                messages=[{"role": "user", "content": prompt}],
            )
            return chat_response.choices[0].message.content.strip()

        except Exception as e:
            print(f"❌ Quick summary error: {e}")
            return f"Internet kamu saat ini {quality}. Ping {ping}ms, Download {download} Mbps, Upload {upload} Mbps."
