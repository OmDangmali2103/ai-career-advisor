from flask import Flask, render_template_string, request
from google import genai
from dotenv import load_dotenv
import os

from pathlib import Path

env_path = Path(__file__).parent / ".env"
print("Looking for .env at:", env_path)
print("Exists:", env_path.exists())

load_dotenv(env_path)

print("API Key:", os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Career Compass AI</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Marked.js CDN for Markdown Parsing -->
    <script src="https://cdn.jsdelivr.net/npm/marked/lib/marked.umd.js"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        gray: {
                            850: '#1f2937',
                            900: '#111827',
                            950: '#030712',
                        }
                    }
                }
            }
        }
    </script>
    <style>
        /* Custom Styling for the AI Output */
        .markdown-body h1, .markdown-body h2, .markdown-body h3 { color: #f3f4f6; font-weight: bold; margin-top: 1.5em; margin-bottom: 0.5em; }
        .markdown-body h1 { font-size: 1.5rem; border-bottom: 1px solid #374151; padding-bottom: 0.3em; }
        .markdown-body h2 { font-size: 1.25rem; }
        .markdown-body h3 { font-size: 1.1rem; color: #60a5fa; }
        .markdown-body p { margin-bottom: 1em; line-height: 1.6; color: #d1d5db; }
        .markdown-body ul { list-style-type: disc; padding-left: 1.5em; margin-bottom: 1em; color: #d1d5db; }
        .markdown-body ol { list-style-type: decimal; padding-left: 1.5em; margin-bottom: 1em; color: #d1d5db; }
        .markdown-body strong { color: #f9fafb; font-weight: 600; }
        .markdown-body code { background-color: #374151; padding: 0.2em 0.4em; border-radius: 0.25rem; font-size: 0.875em; }
    </style>
</head>
<body class="bg-gray-950 text-gray-200 min-h-screen font-sans antialiased flex flex-col items-center pt-16 pb-24 px-4">

    <!-- Header Section -->
    <div class="max-w-3xl w-full text-center mb-10">
        <h1 class="text-4xl font-extrabold tracking-tight text-white mb-4">Career Compass AI</h1>
        <p class="text-lg text-gray-400">Empowering your professional journey with tailored pathways, skill gap analysis, and strategic action plans.</p>
    </div>

    <div class="max-w-3xl w-full grid grid-cols-1 md:grid-cols-1 gap-8">
        
        <!-- Input Form Card -->
        <div class="bg-gray-900 border border-gray-800 rounded-2xl shadow-xl p-8 relative overflow-hidden">
            <!-- Decorative Top Gradient -->
            <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500"></div>
            
            <form id="advisorForm" method="POST" onsubmit="showLoader()">
                
                <div class="space-y-6">
                    
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label for="current_role" class="block text-sm font-medium text-gray-400 mb-1">Current Status</label>
                            <input type="text" id="current_role" name="current_role" required placeholder="e.g., 3rd Year Engineering Student" 
                                class="w-full bg-gray-950 border border-gray-700 text-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 block px-4 py-3 outline-none"
                                {% if current_role %}value="{{ current_role }}"{% endif %}>
                        </div>
                        <div>
                            <label for="target_industry" class="block text-sm font-medium text-gray-400 mb-1">Target Career Goal</label>
                            <input type="text" id="target_industry" name="target_industry" required placeholder="e.g., Data Engineer" 
                                class="w-full bg-gray-950 border border-gray-700 text-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 block px-4 py-3 outline-none"
                                {% if target_industry %}value="{{ target_industry }}"{% endif %}>
                        </div>
                    </div>

                    <div>
                        <label for="skills" class="block text-sm font-medium text-gray-400 mb-1">Your Current Skills</label>
                        <textarea id="skills" name="skills" required placeholder="e.g., Python, SQL, Basic Excel..." rows="3" 
                            class="w-full bg-gray-950 border border-gray-700 text-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 block px-4 py-3 outline-none resize-none">{% if skills %}{{ skills }}{% endif %}</textarea>
                    </div>
                </div>

                <div class="mt-8">
                    <!-- Submit Button -->
                    <button type="submit" id="submitBtn" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 px-6 rounded-lg transition-all shadow-lg shadow-blue-500/30 flex items-center justify-center gap-2">
                        <span>Run Agentic Analysis</span>
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                          <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd" />
                        </svg>
                    </button>
                    
                    <!-- Loading State Spinner -->
                    <div id="loadingState" class="hidden w-full bg-gray-800 text-gray-300 font-semibold py-3 px-6 rounded-lg flex items-center justify-center gap-3">
                        <svg class="animate-spin h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span>Agent is analyzing profile and computing roadmap...</span>
                    </div>
                </div>
            </form>
        </div>

        {% if error_text %}
        <!-- Error Message Card -->
        <div class="bg-red-900/50 border border-red-500/50 text-red-200 rounded-xl p-6 shadow-lg">
            <h3 class="font-bold flex items-center gap-2 mb-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                </svg>
                Error Processing Request
            </h3>
            <p class="text-sm opacity-90">{{ error_text }}</p>
        </div>
        {% endif %}

        {% if response_text %}
        <!-- Output Content Card -->
        <div class="bg-gray-900 border border-gray-800 rounded-2xl shadow-xl p-8 mt-4 relative overflow-hidden" id="resultsCard">
            <!-- Decorative Top Gradient -->
            <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 to-teal-500"></div>
            
            <div class="flex items-center gap-3 mb-6 border-b border-gray-800 pb-4">
                <div class="bg-emerald-500/20 p-2 rounded-lg text-emerald-400">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </div>
                <h2 class="text-2xl font-bold text-white">Agent Output & Action Plan</h2>
            </div>
            
            <!-- This is where Marked.js injects the formatted HTML -->
            <div id="markdownContent" class="markdown-body"></div>
            
            <!-- Hidden raw text field for Javascript parsing -->
            <textarea id="rawMarkdown" class="hidden">{{ response_text }}</textarea>
        </div>
        {% endif %}
    </div>

    <!-- Interactive Logic Scripts -->
    <script>
        // Swaps the button for a spinning loader
        function showLoader() {
            document.getElementById('submitBtn').classList.add('hidden');
            document.getElementById('loadingState').classList.remove('hidden');
            document.getElementById('loadingState').classList.add('flex');
            
            // Scroll slightly up so the user can see the loading state
            document.getElementById('advisorForm').scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        // Parses the raw markdown generated by the AI into styled HTML elements
        document.addEventListener("DOMContentLoaded", function() {
            const rawMarkdownElement = document.getElementById('rawMarkdown');
            if (rawMarkdownElement) {
                const rawText = rawMarkdownElement.value;
                const renderedHtml = marked.parse(rawText);
                document.getElementById('markdownContent').innerHTML = renderedHtml;
                
                // Automatically scroll down to the results card when the page reloads
                document.getElementById('resultsCard').scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    response_text = None
    error_text = None

    current_role = ""
    skills = ""
    target_industry = ""

    if request.method == "POST":
        current_role = request.form.get("current_role", "")
        skills = request.form.get("skills", "")
        target_industry = request.form.get("target_industry", "")

        try:
            api_key = os.getenv("GEMINI_API_KEY")

            if not api_key:
                raise Exception(
                    "GEMINI_API_KEY not found. Create a .env file and add your API key."
                )

            client = genai.Client(api_key=api_key)

            agent_prompt = f"""
You are an expert AI Career Advisor.

Analyze the profile below and provide a professional career roadmap.

Current Status:
{current_role}

Current Skills:
{skills}

Target Career:
{target_industry}

Provide:

# Career Assessment

# Skill Gap Analysis

# 90-Day Learning Roadmap

# Recommended Courses

# Two Portfolio Projects

# Resume Improvement Tips

# Interview Preparation Strategy
"""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=agent_prompt,
            )

            response_text = response.text

        except Exception as e:
            error_text = str(e)

    return render_template_string(
        HTML_TEMPLATE,
        response_text=response_text,
        error_text=error_text,
        current_role=current_role,
        skills=skills,
        target_industry=target_industry,
    )

if __name__ == "__main__":
    app.run(
    host="127.0.0.1",
    port=5000,
    debug=False,
    use_reloader=False
)