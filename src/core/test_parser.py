import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class TestParser:
    """
    Extracts requirements from test code to provide feedback to the AI.
    It identifies critical HTML IDs, tags, CSS classes, and required text
    that the implementation MUST satisfy.
    """

    @staticmethod
    def extract_requirements(test_code: str) -> Dict[str, List[str]]:
        """
        Parses test code and extracts concrete requirements using regular expressions.

        Args:
            test_code: The source code of the test file.

        Returns:
            A dictionary containing lists of required_ids, required_tags,
            required_classes, and required_text.
        """
        requirements = {
            'required_ids': [],
            'required_tags': [],
            'required_classes': [],
            'required_text': []
        }

        if not test_code:
            return requirements

        try:
            # 1. Extract HTML IDs
            # Direct id attribute: id="work" or id='home'
            requirements['required_ids'].extend(re.findall(r'id=["\']([^"\']+)["\']', test_code))

            # Lists of IDs: required_ids = ["home", "work"]
            id_list_match = re.search(r'required_ids\s*=\s*\[(.*?)\]', test_code, re.DOTALL)
            if id_list_match:
                ids_str = id_list_match.group(1)
                requirements['required_ids'].extend(re.findall(r'["\']([^"\']+)["\']', ids_str))

            # 2. Extract HTML Tags
            # BeautifulSoup find/find_all: soup.find("section", ...)
            requirements['required_tags'].extend(re.findall(r'soup\.find(?:_all)?\(["\']([^"\']+)["\']', test_code))

            # Lists of tags: required_tags = ["header", "nav"]
            tag_list_match = re.search(r'required_tags\s*=\s*\[(.*?)\]', test_code, re.DOTALL)
            if tag_list_match:
                tags_str = tag_list_match.group(1)
                requirements['required_tags'].extend(re.findall(r'["\']([^"\']+)["\']', tags_str))

            # 3. Extract CSS Classes
            # class_="my-class" or class='my-class'
            requirements['required_classes'].extend(re.findall(r'class(?:_)?=["\']([^"\']+)["\']', test_code))

            # Lists of classes: required_classes = ["btn", "active"]
            class_list_match = re.search(r'required_classes\s*=\s*\[(.*?)\]', test_code, re.DOTALL)
            if class_list_match:
                classes_str = class_list_match.group(1)
                requirements['required_classes'].extend(re.findall(r'["\']([^"\']+)["\']', classes_str))

            # 4. Extract Required Text Assertions
            # assert "Hello World" in ...
            requirements['required_text'].extend(re.findall(r'assert\s+["\']([^"\']+)["\']\s+in', test_code))

            # Verify text: .get_text() comparisons
            requirements['required_text'].extend(re.findall(r'==\s*["\']([^"\']+)["\']', test_code))

            # 5. Extract Attr Checks (e.g. href="#work")
            requirements['required_text'].extend(re.findall(r'\[[\"\']href[\"\']\]\s*==\s*["\']([^"\']+)["\']', test_code))

            # Cleanup, deduplicate and filter
            common_non_tags = {'html.parser', 'lxml', 'xml', 'utf-8', 'utf8'}

            for key in requirements:
                # Deduplicate and sort
                unique_vals = sorted(list(set([str(val).strip() for val in requirements[key] if val])))

                # Filter noise
                if key == 'required_tags':
                    unique_vals = [t for t in unique_vals if t.islower() and t not in common_non_tags and len(t) < 20]
                elif key == 'required_ids':
                    unique_vals = [i for i in unique_vals if len(i) < 50]
                elif key == 'required_classes':
                    unique_vals = [c for c in unique_vals if len(c) < 50]

                requirements[key] = unique_vals

        except Exception as e:
            logger.error(f"Error parsing test requirements: {e}")

        return requirements
