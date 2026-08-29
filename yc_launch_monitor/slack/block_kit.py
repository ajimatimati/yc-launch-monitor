import datetime
from typing import Dict, Any, List
from ..models import LaunchItem, LaunchStatus, LaunchSource, ProgramType

class SlackBlockBuilder:
    """
    Constructs high-impact, professional Slack Block Kit message payloads
    customized for GTM outreach and pipeline intelligence.
    """

    @classmethod
    def build_alert_payload(cls, item: LaunchItem) -> Dict[str, Any]:
        """Builds full Slack Block Kit payload with fallback text and interactive blocks."""
        is_early = item.status == LaunchStatus.EARLY_SIGNAL
        is_speedrun = item.program_type == ProgramType.SPEEDRUN

        # Header title
        if is_early:
            if is_speedrun:
                header_text = "⚡ EARLY SPEEDRUN SIGNAL: Founder Announced Before Directory"
            else:
                header_text = "🔥 EARLY YC SIGNAL: Founder Announced Before YC"
        else:
            if is_speedrun:
                header_text = "🚀 NEW SPEEDRUN COMPANY LAUNCH"
            else:
                header_text = "✅ NEW YC COMPANY: CONFIRMED BY YC"

        # Format detection timestamp in PT / UTC
        dt_str = item.detected_at.strftime("%b %d, %Y, %I:%M %p UTC")

        # Founder details
        founder_str = item.display_founder
        if item.founders and item.founders[0].profile_url:
            founder_str = f"<{item.founders[0].profile_url}|{founder_str}>"

        # Source badge
        source_labels = {
            LaunchSource.X_TWITTER: "X (Twitter)",
            LaunchSource.LINKEDIN: "LinkedIn",
            LaunchSource.YC_DIRECTORY: "YC Directory",
            LaunchSource.SPEEDRUN_DIRECTORY: "Speedrun Directory"
        }
        source_label = source_labels.get(item.source, str(item.source.value))

        # Status text
        if is_early:
            status_text = "⚡ *Founder announced / not yet officially announced by YC*"
        else:
            status_text = "✅ *Confirmed Official Directory Listing*"

        # Company link
        if item.website:
            company_display = f"*<{item.website}|{item.company_name}>*"
        else:
            company_display = f"*{item.company_name}*"

        # Construct Blocks
        blocks: List[Dict[str, Any]] = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": header_text,
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Company:*\n{company_display}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Founder:*\n{founder_str}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Batch:*\n`{item.batch or 'YC Current'}`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Source:*\n{source_label}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Status:* {status_text}"
                }
            }
        ]

        # Post Quote or Description block
        if item.post_text:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Original Post:*\n> \"_{item.post_text.strip()}_\""
                }
            })
        elif item.description:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{item.description}"
                }
            })

        # Links & Meta context
        links_parts = []
        if item.post_url:
            links_parts.append(f"🔗 *Original Post:* <{item.post_url}|View on {source_label}>")
        if item.website:
            links_parts.append(f"🌐 *Website:* <{item.website}|{item.website}>")
        if item.slug and item.program_type == ProgramType.YC:
            links_parts.append(f"📙 *YC Profile:* <https://www.ycombinator.com/companies/{item.slug}|ycombinator.com/{item.slug}>")

        if links_parts:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "\n".join(links_parts)
                }
            })

        # Context footer (Timestamp + Rho GTM Tag)
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"🕒 *Detected:* {dt_str}  |  🎯 *Rho Pipeline Radar*  |  🤖 *Pond Agent*"
                }
            ]
        })

        # Interactive Actions Block (Buttons)
        action_elements = []
        if item.post_url:
            action_elements.append({
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "📱 Open Post",
                    "emoji": True
                },
                "url": item.post_url,
                "style": "primary"
            })
        if item.website:
            action_elements.append({
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "🌐 Visit Website",
                    "emoji": True
                },
                "url": item.website
            })

        if action_elements:
            blocks.append({
                "type": "actions",
                "elements": action_elements
            })

        blocks.append({"type": "divider"})

        # Plaintext fallback for mobile notifications
        fallback_text = f"{header_text}: {item.company_name} ({item.batch or 'YC'}) - {source_label}"

        return {
            "text": fallback_text,
            "blocks": blocks
        }
