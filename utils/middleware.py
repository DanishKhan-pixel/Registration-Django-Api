import os

from dotenv import load_dotenv
from django.utils.deprecation import MiddlewareMixin


class ModifyHTMLMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        load_dotenv()

        # Check if response is HTML
        if "text/html" in response.get("Content-Type", ""):
            content = response.content.decode("utf-8")  # Convert bytes to string

            # CSS variables to inject
            script = """
      <script>
        document.documentElement.style.setProperty('--secondary', 'rgba(96, 171, 154, 1)');
        document.documentElement.style.setProperty('--primary-fg', 'rgba(0, 0, 0, 1)');
        document.documentElement.style.setProperty('--accent', 'rgba(255, 255, 255, 1)');
        document.documentElement.style.setProperty('--link-fg', 'rgba(96, 171, 154, 1)');
        document.documentElement.style.setProperty('--breadcrumbs-bg', 'rgba(76, 136, 123, 1)');
      </script>
      """

            # Insert script after body tag
            if "</body>" in content:
                content = content.replace("</body>", f"</body>{script}")

            if "Django administration" in content:
                content = content.replace(
                    "Django administration", os.environ.get("MICROSERVICE_NAME", "Authentication")
                )

            response.content = content.encode("utf-8")  # Convert back to bytes

        return response
