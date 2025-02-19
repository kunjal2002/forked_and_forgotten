from github import Github
import datetime
import pandas as pd
import numpy as np

# Replace with your GitHub Personal Access Token
GITHUB_TOKEN = "YOUR_TOKEN"
g = Github(GITHUB_TOKEN)


# Function to recursively count files and lines of code
def count_files_and_loc(repo, path=""):
    contents = repo.get_contents(path)
    total_files = 0
    total_loc = 0

    for content in contents:
        if content.type == "file":
            total_files += 1
            try:
                total_loc += len(content.decoded_content.splitlines())
            except:
                pass  # Handle binary or inaccessible files
        elif content.type == "dir":
            files, loc = count_files_and_loc(repo, content.path)
            total_files += files
            total_loc += loc

    return total_files, total_loc


# Function to collect data for a given repository
def get_repo_data(repo_name):
    repo = g.get_repo(repo_name)
    contributors = repo.get_contributors()
    issues = repo.get_issues(state='all')
    pull_requests = repo.get_pulls(state='all')

    stars = repo.stargazers_count
    forks = repo.forks_count
    total_files, loc = count_files_and_loc(repo)

    open_issues = repo.get_issues(state='open').totalCount
    closed_issues = repo.get_issues(state='closed').totalCount
    issue_resolution_rate = closed_issues / (open_issues + closed_issues) if (open_issues + closed_issues) > 0 else 0

    contributor_data = []

    for contributor in contributors:
        contributions = repo.get_stats_contributors()

        if contributions:
            for stat in contributions:
                if stat.author.login == contributor.login:
                    contribution_weeks = [week.w for week in stat.weeks if week.c > 0]

                    if contribution_weeks:
                        first_contribution = min(contribution_weeks)
                        last_contribution = max(contribution_weeks)
                        frequency = len(contribution_weeks)

                        # Calculate retention in weeks
                        retention = (last_contribution - first_contribution).days / 7

                        # Determine experience and activity
                        experience = "New" if stat.total < 10 else "Experienced"
                        is_active = "Active" if stat.total > 10 and len(contribution_weeks) >= 12 else "Passive"

                    contributor_data.append({
                            "Contributor": contributor.login,
                            "First Contribution": (first_contribution).replace(tzinfo=None),
                            "Last Contribution": (last_contribution).replace(tzinfo=None),
                            "Total Contributions": stat.total,
                            "Frequency": frequency,
                            "Retention (weeks)": retention,
                            "Experience": experience,
                            "Status": is_active
                        })

    repo_data = {
        "Repository": repo_name,
        "Stars": stars,
        "Forks": forks,
        "Total Issues": issues.totalCount,
        "Total Pull Requests": pull_requests.totalCount,
        "Total Files": total_files,
        "Lines of Code": loc,
        "Contributors": contributor_data,
        "Open Issues": open_issues,
        "Closed Issues": closed_issues,
        "Issue Resolution Ratio": issue_resolution_rate
    }

    return repo_data


# Example usage
repo_name = "codecrafters-io/build-your-own-x"  # Updated to target repository
repo_data = get_repo_data(repo_name)

# Convert to DataFrame
columns = ["Contributor", "First Contribution", "Last Contribution", "Total Contributions", "Frequency", "Retention (weeks)", "Experience"]
df = pd.DataFrame(repo_data['Contributors'], columns=columns)
print(df)
print('--------------------------------------------')
contributors_data = repo_data.pop('Contributors')  # Extract 'Contributors'

# Step 2: Create a DataFrame from the 'Contributors' data
contributors_df = pd.DataFrame(contributors_data)

# Step 3: Create a DataFrame from the remaining `repo_data`
repo_metadata = pd.DataFrame([repo_data])  # Wrap in a list to create a single-row DataFrame

# Step 4: Concatenate or merge DataFrames if needed
result_df = pd.concat([repo_metadata] * len(contributors_df), ignore_index=True)  # Repeat metadata
final_df = pd.concat([contributors_df, result_df], axis=1)

# Display the final DataFrame
print(final_df)# Data Cleaning: Handling missing values
# contributors_df.fillna({'Total Contributions': 0, 'Frequency': 0, 'Retention (weeks)': 0}, inplace=True)

# Save to Excel
output_file = "repo_contributor_data.xlsx"
final_df.to_excel(output_file, index=False)
print(f"Data saved to {output_file}")
