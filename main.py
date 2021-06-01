import os
import zulip
from github import Github

GITHUB_ACCOUNT = os.environ['GITHUB_ACCOUNT']

zulip_client = zulip.Client(config_file="./zuliprc")
github = Github(os.environ['GITHUB_TOKEN'])


def create(msg):
    if msg['type'] != "message":
        return
    msg = msg['message']
    if msg['type'] != "stream":
        request = {
            "type": "private",
            "to": [msg['sender_id']],
            "content": "You can only create issues in Streams",
        }
        zulip_client.send_message(request)
        return
    topic = msg['subject']
    stream = msg['stream_id']
    resp = zulip_client.get_messages({
        "anchor": "newest",
        "num_before": 200,
        "num_after": 0,
        "narrow": [
            {"operator": "stream", "operand": stream},
            {"operator": "topic", "operand": topic}
        ]
    })
    content = ""
    for message in resp['messages']:
        if '@issue' in message['content']:
            continue
        content = content + "**" + message['sender_full_name'] + "**: " + message['content'] + "<br>"
    content = content.replace("@", "[at]")
    repo_name = GITHUB_ACCOUNT + "/" + msg['content'].replace("@**issue** ", "")
    repo = github.get_repo(repo_name)
    if repo is None:
        zulip_client.send_message({
            "type": "stream",
            "to": stream,
            "topic": topic,
            "content": "Repository does not exists.",
        })
        return
    issue = repo.create_issue(topic, content)
    zulip_client.send_message({
        "type": "stream",
        "to": stream,
        "topic": topic,
        "content": "Issue created. [" + repo_name + "#" + str(issue.number) + "](https://github.com/" + repo_name + "/issues/" + str(issue.number) + ")",
    })
    print("Created " + repo_name + "#" + str(issue.number))


zulip_client.call_on_each_event(create, narrow=[['is', 'mentioned']], event_types=['message'])
