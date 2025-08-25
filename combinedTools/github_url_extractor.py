
import re


def find_github_urls(data):
    """
    Extracts GitHub URLs from a dictionary of attendee data.
    This version safely handles cases where enrichment fails.
    """
    if hasattr(data, "model_dump"):
        data = data.model_dump()

    github_urls = []
    engineer_keywords = [
        "developer",
        "engineer",
        "software",
        "full-stack",
        "web dev",
        "ai",
        "data science",
    ]

    for attendee in data.get("attendees", []):
        enriched_info = attendee.get("enriched", {})

        if not isinstance(enriched_info, dict):
            print(
                f"Skipping attendee '{attendee.get('name')}' due to an enrichment error."
            )
            continue  

        profile_text = (
            enriched_info.get("occupation", "")
            + " "
            + enriched_info.get("headline", "")
        ).lower()
        is_engineer = any(keyword in profile_text for keyword in engineer_keywords)

        if is_engineer:
            summary = enriched_info.get("summary", "")
            if summary:
                match = re.search(r"(https?://github\.com/[\w-]+)", summary)
                if match:
                    github_urls.append(match.group(0))
    return github_urls


# --- Correct Way to Test ---
# This block now simulates receiving a raw JSON string from an API (like Apify).

# 1. Define the raw data as a string, with lowercase 'true' and 'false'.
# test_json_string = """
# {
#     "meeting_title": "PORTIA TESTING Meet",
#     "organizer_email": "anuj846k@gmail.com",
#     "attendees": [
#         {
#             "name": "Kshitij Akarsh",
#             "email": "kshitijakarsh@gmail.com",
#             "enriched": {
#                 "occupation": "B.Tech CSE 27 | Web Developer | 1x Hackathon Winner 🏆 | UI/UX Designer",
#                 "headline": "B.Tech CSE 27 | Web Developer | 1x Hackathon Winner 🏆 | UI/UX Designer",
#                 "summary": "I am a Computer Science (Data Science) undergraduate skilled in JavaScript, TypeScript, Python...\\n\\nhere's my github : https://github.com/kshitijakarsh",
#                 "student": false,
#                 "following": true,
#                 "followable": true
#             }
#         },
#         {
#             "name": "Mounir Mouawad",
#             "email": "mounir.mouawad@gmail.com",
#             "enriched": {
#                 "occupation": "Co-founder / CEO at Portia AI",
#                 "headline": "Co-founder / CEO at Portia AI",
#                 "summary": "I'm a co-founder of a company. here is my github : https://github.com/mounirmouawad",
#                 "student": false,
#                 "following": true,
#                 "followable": true
#             }
#         }
#     ]
# }
# """

# # 2. Parse the string into a Python dictionary. This is the crucial step.
# # json.loads() acts as a translator from the JSON string language to the Python dictionary language.
# test_data_as_dict = json.loads(test_json_string)
# print(test_data_as_dict)
# # 3. Pass the resulting dictionary to your function.
# result = find_github_urls(test_data_as_dict)

# # 4. Print the result.
# print(result)
