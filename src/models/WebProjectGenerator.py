import os
import logging
from typing import Dict, Any


class WebProjectGenerator:
    """
    Handles the generation of web projects (HTML, CSS, JS) based on AI responses.
    """

    def __init__(self, project_path: str, log_output_fn=None):
        self.project_path = project_path
        self.log_output = log_output_fn or (lambda msg: logging.info(msg))

    def generate_web_project(self, metadata: Dict[str, Any], prompt: str) -> bool:
        """
        Generate a web project based on metadata and prompt.
        Returns True if successful, False otherwise.
        """
        try:
            self.log_output("Generating web project structure...")

            # Create web directories
            web_root = os.path.join(self.project_path, "web")
            css_dir = os.path.join(web_root, "css")
            js_dir = os.path.join(web_root, "js")
            img_dir = os.path.join(web_root, "images")

            os.makedirs(web_root, exist_ok=True)
            os.makedirs(css_dir, exist_ok=True)
            os.makedirs(js_dir, exist_ok=True)
            os.makedirs(img_dir, exist_ok=True)

            # Check if project type is web-related
            is_web_project = self._is_web_project(metadata, prompt)
            if not is_web_project:
                self.log_output("Project not identified as web project. Skipping web file generation.")
                return False

            # Generate base files
            self._generate_html_file(web_root, metadata, prompt)
            self._generate_css_file(css_dir, metadata)
            self._generate_js_file(js_dir, metadata)

            # Generate additional content if needed
            if "web_components" in metadata:
                self._generate_components(web_root, metadata["web_components"])

            self.log_output("Web project generated successfully!")
            return True

        except Exception as e:
            logging.error(f"Failed to generate web project: {e}")
            self.log_output(f"Error generating web project: {e}")
            return False

    def _is_web_project(self, metadata: Dict[str, Any], prompt: str) -> bool:
        """Determine if this is a web project based on metadata and prompt"""
        # Check metadata for web indicators
        if metadata.get("project_type", "").lower() in ["web", "website", "html", "frontend"]:
            return True

        # Check if any web technologies are mentioned in key_features
        web_techs = ["html", "css", "js", "javascript", "web", "website", "responsive"]
        for feature in metadata.get("key_features", []):
            if any(tech in feature.lower() for tech in web_techs):
                return True

        # Check raw prompt for web indicators
        web_keywords = ["html", "website", "webpage", "web page", "site", "css", "javascript"]
        if any(keyword in prompt.lower() for keyword in web_keywords):
            return True

        return False

    def _generate_html_file(self, web_root: str, metadata: Dict[str, Any], prompt: str) -> None:
        """Generate the main HTML file"""
        # Extract name from prompt or metadata
        name = self._extract_name(metadata, prompt) or "John Doe"
        title = metadata.get("project_name", f"{name}'s Portfolio")

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header>
        <nav>
            <div class="logo">{name}</div>
            <ul>
                <li><a href="#home">Home</a></li>
                <li><a href="#portfolio">Portfolio</a></li>
                <li><a href="#about">About</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </nav>
    </header>

    <section id="home" class="hero">
        <div class="hero-content">
            <h1>Hi, I'm {name}</h1>
            <h2>Designer & Creative Professional</h2>
            <p>Creating beautiful, functional designs that solve real problems.</p>
            <a href="#portfolio" class="cta-button">View My Work</a>
        </div>
    </section>

    <section id="portfolio" class="portfolio">
        <h2>My Portfolio</h2>
        <div class="portfolio-grid">
            <div class="portfolio-item">
                <img src="images/placeholder1.jpg" alt="Project 1">
                <h3>Project One</h3>
                <p>Brand Identity</p>
            </div>
            <div class="portfolio-item">
                <img src="images/placeholder2.jpg" alt="Project 2">
                <h3>Project Two</h3>
                <p>Website Design</p>
            </div>
            <div class="portfolio-item">
                <img src="images/placeholder3.jpg" alt="Project 3">
                <h3>Project Three</h3>
                <p>Mobile App</p>
            </div>
        </div>
    </section>

    <section id="about" class="about">
        <h2>About Me</h2>
        <div class="about-content">
            <div class="about-text">
                <p>I am a passionate designer with a keen eye for detail and a love for creating meaningful experiences. With years of experience in digital and print design, I bring creativity and technical expertise to every project.</p>
                <p>My approach combines aesthetic sensibility with user-centered design principles to create work that is both beautiful and functional.</p>
            </div>
        </div>
    </section>

    <section id="contact" class="contact">
        <h2>Get In Touch</h2>
        <div class="contact-form">
            <form>
                <div class="form-group">
                    <input type="text" placeholder="Name" required>
                </div>
                <div class="form-group">
                    <input type="email" placeholder="Email" required>
                </div>
                <div class="form-group">
                    <textarea placeholder="Your Message" rows="5" required></textarea>
                </div>
                <button type="submit" class="submit-btn">Send Message</button>
            </form>
        </div>
    </section>

    <footer>
        <p>&copy; {metadata.get('year', '2025')} {name}. All rights reserved.</p>
    </footer>

    <script src="js/main.js"></script>
</body>
</html>
"""
        index_path = os.path.join(web_root, "index.html")
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        self.log_output(f"Created HTML file: index.html")

    def _generate_css_file(self, css_dir: str, metadata: Dict[str, Any]) -> None:
        """Generate the CSS file"""
        # Determine color scheme from metadata or use default
        colors = metadata.get("color_scheme", {
            "primary": "#2c3e50",
            "secondary": "#3498db",
            "text": "#333333",
            "background": "#ffffff",
            "accent": "#e74c3c"
        })

        if isinstance(colors, list) and len(colors) >= 3:
            color_dict = {
                "primary": colors[0],
                "secondary": colors[1],
                "accent": colors[2],
                "text": "#333333",
                "background": "#ffffff"
            }
            colors = color_dict

        css_content = f"""/* Main Stylesheet */
:root {{
    --primary-color: {colors.get("primary", "#2c3e50")};
    --secondary-color: {colors.get("secondary", "#3498db")};
    --text-color: {colors.get("text", "#333333")};
    --bg-color: {colors.get("background", "#ffffff")};
    --accent-color: {colors.get("accent", "#e74c3c")};
}}

* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--bg-color);
}}

/* Navigation */
header {{
    background-color: var(--primary-color);
    padding: 1rem 5%;
    position: fixed;
    width: 100%;
    z-index: 100;
}}

nav {{
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.logo {{
    color: white;
    font-size: 1.5rem;
    font-weight: bold;
}}

nav ul {{
    display: flex;
    list-style: none;
}}

nav ul li {{
    margin-left: 2rem;
}}

nav ul li a {{
    color: white;
    text-decoration: none;
    transition: opacity 0.3s;
}}

nav ul li a:hover {{
    opacity: 0.8;
}}

/* Hero Section */
.hero {{
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: var(--primary-color);
    color: white;
    padding: 0 5%;
    text-align: center;
}}

.hero-content {{
    max-width: 800px;
}}

.hero h1 {{
    font-size: 3rem;
    margin-bottom: 1rem;
}}

.hero h2 {{
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
    font-weight: 300;
}}

.hero p {{
    font-size: 1.1rem;
    margin-bottom: 2rem;
}}

.cta-button {{
    display: inline-block;
    padding: 0.8rem 2rem;
    background-color: var(--accent-color);
    color: white;
    text-decoration: none;
    border-radius: 4px;
    transition: background-color 0.3s;
}}

.cta-button:hover {{
    background-color: var(--secondary-color);
}}

/* Portfolio Section */
.portfolio {{
    padding: 6rem 5%;
    text-align: center;
}}

.portfolio h2, .about h2, .contact h2 {{
    font-size: 2.5rem;
    margin-bottom: 3rem;
    color: var(--primary-color);
}}

.portfolio-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 2rem;
}}

.portfolio-item {{
    background-color: #f9f9f9;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}}

.portfolio-item:hover {{
    transform: translateY(-5px);
}}

.portfolio-item img {{
    width: 100%;
    height: 200px;
    object-fit: cover;
}}

.portfolio-item h3 {{
    margin: 1rem 0 0.5rem;
    color: var(--primary-color);
}}

.portfolio-item p {{
    margin-bottom: 1rem;
    color: #666;
}}

/* About Section */
.about {{
    padding: 6rem 5%;
    background-color: #f9f9f9;
    text-align: center;
}}

.about-content {{
    max-width: 800px;
    margin: 0 auto;
}}

.about p {{
    margin-bottom: 1.5rem;
    font-size: 1.1rem;
}}

/* Contact Section */
.contact {{
    padding: 6rem 5%;
    text-align: center;
}}

.contact-form {{
    max-width: 600px;
    margin: 0 auto;
}}

.form-group {{
    margin-bottom: 1.5rem;
}}

input, textarea {{
    width: 100%;
    padding: 1rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-family: inherit;
    font-size: 1rem;
}}

.submit-btn {{
    background-color: var(--secondary-color);
    color: white;
    border: none;
    padding: 1rem 2rem;
    font-size: 1rem;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s;
}}

.submit-btn:hover {{
    background-color: var(--primary-color);
}}

/* Footer */
footer {{
    background-color: var(--primary-color);
    color: white;
    text-align: center;
    padding: 2rem 0;
}}

/* Responsive Design */
@media (max-width: 768px) {{
    .hero h1 {{
        font-size: 2.5rem;
    }}

    .portfolio-grid {{
        grid-template-columns: 1fr;
    }}

    nav {{
        flex-direction: column;
    }}

    nav ul {{
        margin-top: 1rem;
    }}

    nav ul li {{
        margin-left: 1rem;
        margin-right: 1rem;
    }}
}}
"""
        css_path = os.path.join(css_dir, "style.css")
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(css_content)

        self.log_output("Created CSS file: css/style.css")

    def _generate_js_file(self, js_dir: str, metadata: Dict[str, Any]) -> None:
        """Generate the JavaScript file"""
        js_content = """// Main JavaScript file

document.addEventListener('DOMContentLoaded', function() {
    console.log('Website loaded successfully!');

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();

            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);

            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Form submission handling
    const contactForm = document.querySelector('.contact-form form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();

            // Get form values
            const name = this.querySelector('input[type="text"]').value;
            const email = this.querySelector('input[type="email"]').value;
            const message = this.querySelector('textarea').value;

            // Simple validation
            if (name && email && message) {
                // In a real application, you would send this data to a server
                alert('Thank you for your message! I will get back to you soon.');
                this.reset();
            } else {
                alert('Please fill out all fields.');
            }
        });
    }
});
"""
        js_path = os.path.join(js_dir, "main.js")
        with open(js_path, 'w', encoding='utf-8') as f:
            f.write(js_content)

        self.log_output("Created JavaScript file: js/main.js")

    def _generate_components(self, web_root: str, components: list) -> None:
        """Generate additional components if specified"""
        for component in components:
            if isinstance(component, dict):
                component_name = component.get("name", "").lower()

                if "gallery" in component_name:
                    self._generate_gallery_component(web_root)
                elif "slider" in component_name:
                    self._generate_slider_component(web_root)
                elif "modal" in component_name:
                    self._generate_modal_component(web_root)

    def _generate_gallery_component(self, web_root: str) -> None:
        """Generate gallery component JS and CSS"""
        # Implementation would go here
        pass

    def _generate_slider_component(self, web_root: str) -> None:
        """Generate slider component JS and CSS"""
        # Implementation would go here
        pass

    def _generate_modal_component(self, web_root: str) -> None:
        """Generate modal component JS and CSS"""
        # Implementation would go here
        pass

    def _extract_name(self, metadata: Dict[str, Any], prompt: str) -> str:
        """Extract the designer's name from metadata or prompt"""
        # Try to get from metadata
        if "designer_name" in metadata:
            return metadata["designer_name"]

        if "person_name" in metadata:
            return metadata["person_name"]

        # Try to extract from project name
        project_name = metadata.get("project_name", "")
        if "portfolio" in project_name.lower() and "for" in project_name.lower():
            parts = project_name.split("for")
            if len(parts) > 1:
                return parts[1].strip()

        # Try to extract from prompt
        if "designer named" in prompt.lower():
            parts = prompt.lower().split("designer named")
            if len(parts) > 1:
                name_part = parts[1].strip().split()
                if len(name_part) >= 2:  # Assuming at least first and last name
                    first_name = name_part[0].capitalize()
                    last_name = name_part[1].capitalize()
                    return f"{first_name} {last_name}"

        # Default to empty string if no name found
        return ""
