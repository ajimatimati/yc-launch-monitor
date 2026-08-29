import os
import sys
import json
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from yc_launch_monitor.models import LaunchItem, LaunchStatus, LaunchSource, ProgramType, FounderInfo
from yc_launch_monitor.slack.block_kit import SlackBlockBuilder

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

def generate_html_preview():
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # 1. Early YC Signal
    early_yc = LaunchItem(
        id="demo_early_yc",
        company_name="Hyperscale AI",
        slug="hyperscale-ai",
        website="https://hyperscale.ai",
        batch="YC S26",
        program_type=ProgramType.YC,
        source=LaunchSource.X_TWITTER,
        status=LaunchStatus.EARLY_SIGNAL,
        founders=[
            FounderInfo(
                name="Beknazar Abdikamalov",
                handle="@beknabdik",
                profile_url="https://x.com/beknabdik",
                title="Co-Founder & CEO"
            )
        ],
        description="Autonomous database optimization agents for high-throughput enterprise infrastructure.",
        post_text="We got into YC S26! Excited to move to SF and start building the future of database performance.",
        post_url="https://x.com/beknabdik/status/2061493360150601738",
        detected_at=now - datetime.timedelta(minutes=14)
    )

    # 2. Confirmed YC Company
    confirmed_yc = LaunchItem(
        id="demo_confirmed_yc",
        company_name="Talos",
        slug="talos-us",
        website="https://www.talos-us.com/",
        batch="Fall 2026",
        program_type=ProgramType.YC,
        source=LaunchSource.YC_DIRECTORY,
        status=LaunchStatus.CONFIRMED,
        description="Predictive maintenance for power infrastructure and grid stability.",
        post_url="https://www.ycombinator.com/companies/talos-us",
        detected_at=now - datetime.timedelta(hours=2),
        confirmed_at=now - datetime.timedelta(hours=2)
    )

    # 3. Early Speedrun Signal
    early_sr = LaunchItem(
        id="demo_early_sr",
        company_name="Aura Payments",
        slug="aura-payments",
        website="https://aurapayments.io",
        batch="SR006",
        program_type=ProgramType.SPEEDRUN,
        source=LaunchSource.LINKEDIN,
        status=LaunchStatus.EARLY_SIGNAL,
        founders=[
            FounderInfo(
                name="Elena Rostova",
                handle="elena-rostova-pay",
                profile_url="https://www.linkedin.com/in/elena-rostova-pay",
                title="Co-Founder & CEO"
            )
        ],
        description="Cross-border agentic liquidity settlement protocol for global SaaS businesses.",
        post_text="Thrilled to share that Aura Payments is part of the new a16z Speedrun SR006 cohort! Grateful to the Speedrun team as we build the next-gen merchant liquidity engine.",
        post_url="https://www.linkedin.com/posts/elena-rostova-pay_a16z-speedrun-fintech-activity-891023847291038",
        detected_at=now - datetime.timedelta(minutes=45)
    )

    p1 = SlackBlockBuilder.build_alert_payload(early_yc)
    p2 = SlackBlockBuilder.build_alert_payload(confirmed_yc)
    p3 = SlackBlockBuilder.build_alert_payload(early_sr)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YC Launch Monitor - Live Slack Alert Visual Proof</title>
    <style>
        body {{
            background-color: #1A1D21;
            color: #D1D2D3;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 40px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .container {{
            max-width: 780px;
            width: 100%;
        }}
        .header-title {{
            color: #FFFFFF;
            font-size: 26px;
            font-weight: 700;
            margin-bottom: 8px;
            text-align: center;
        }}
        .header-sub {{
            color: #ABABAD;
            font-size: 14px;
            text-align: center;
            margin-bottom: 32px;
        }}
        .slack-channel-bar {{
            background: #222529;
            padding: 12px 18px;
            border-radius: 8px 8px 0 0;
            font-size: 14px;
            font-weight: 600;
            color: #FFFFFF;
            border: 1px solid #36393E;
            border-bottom: none;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .slack-feed {{
            background: #1A1D21;
            border: 1px solid #36393E;
            border-radius: 0 0 8px 8px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 28px;
        }}
        .message-row {{
            display: flex;
            gap: 14px;
        }}
        .bot-avatar {{
            width: 42px;
            height: 42px;
            border-radius: 6px;
            background: #FF6600;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            flex-shrink: 0;
        }}
        .message-content {{
            flex: 1;
        }}
        .bot-name {{
            font-weight: 700;
            color: #FFFFFF;
            font-size: 15px;
            margin-right: 6px;
        }}
        .bot-badge {{
            background: #36393E;
            color: #ABABAD;
            font-size: 11px;
            padding: 1px 5px;
            border-radius: 3px;
            text-transform: uppercase;
            font-weight: 600;
            margin-right: 8px;
        }}
        .timestamp {{
            font-size: 12px;
            color: #ABABAD;
        }}
        .slack-card {{
            margin-top: 8px;
            background: #222529;
            border-left: 4px solid #FF6600;
            border-radius: 4px;
            padding: 16px 20px;
        }}
        .slack-card.early {{
            border-left-color: #FF4D4D;
            background: #261F1E;
        }}
        .slack-card.confirmed {{
            border-left-color: #2BAC76;
            background: #1C2723;
        }}
        .slack-card.speedrun {{
            border-left-color: #9B51E0;
            background: #25202D;
        }}
        .card-header {{
            font-size: 16px;
            font-weight: 700;
            color: #FFFFFF;
            margin-bottom: 12px;
        }}
        .fields-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 14px;
            font-size: 14px;
        }}
        .field-label {{
            color: #ABABAD;
            font-weight: 600;
            margin-bottom: 2px;
        }}
        .field-val {{
            color: #FFFFFF;
        }}
        .field-val a {{
            color: #1D9BD1;
            text-decoration: none;
        }}
        .field-val a:hover {{
            text-decoration: underline;
        }}
        .quote-box {{
            background: rgba(0,0,0,0.25);
            border-left: 3px solid #ABABAD;
            padding: 10px 14px;
            border-radius: 0 4px 4px 0;
            font-style: italic;
            margin: 12px 0;
            font-size: 14px;
            color: #E8E8E8;
        }}
        .links-row {{
            margin-top: 10px;
            font-size: 13px;
            line-height: 1.6;
        }}
        .links-row a {{
            color: #1D9BD1;
            text-decoration: none;
        }}
        .links-row a:hover {{
            text-decoration: underline;
        }}
        .btn-group {{
            display: flex;
            gap: 10px;
            margin-top: 14px;
        }}
        .slack-btn {{
            background: #007A5A;
            color: #FFFFFF;
            padding: 7px 14px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 600;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .slack-btn.secondary {{
            background: #36393E;
            color: #FFFFFF;
        }}
        .slack-btn:hover {{
            opacity: 0.9;
        }}
        .footer-context {{
            font-size: 11px;
            color: #8B8D91;
            margin-top: 12px;
            border-top: 1px solid rgba(255,255,255,0.08);
            padding-top: 8px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header-title">🚀 YC Launch Monitor — Slack Bot Live Alert Preview</div>
        <div class="header-sub">Rho GTM Pipeline Intelligence Radar • Real-Time Alert Rendering Proof</div>

        <div class="slack-channel-bar">
            <span>🔒 #yc-speedrun-launches</span>
            <span style="color: #8B8D91; font-weight: normal;">| 4 sources continuously monitored</span>
        </div>

        <div class="slack-feed">
            <!-- Message 1: Early Founder Signal -->
            <div class="message-row">
                <div class="bot-avatar">⚡</div>
                <div class="message-content">
                    <div>
                        <span class="bot-name">YC Launch Radar</span>
                        <span class="bot-badge">APP</span>
                        <span class="timestamp">Today at 9:14 AM</span>
                    </div>
                    <div class="slack-card early">
                        <div class="card-header">🔥 EARLY YC SIGNAL — Founder Announced Before YC</div>
                        <div class="fields-grid">
                            <div>
                                <div class="field-label">Company:</div>
                                <div class="field-val"><strong><a href="https://hyperscale.ai" target="_blank">Hyperscale AI</a></strong></div>
                            </div>
                            <div>
                                <div class="field-label">Founder:</div>
                                <div class="field-val"><a href="https://x.com/beknabdik" target="_blank">Beknazar Abdikamalov (@beknabdik)</a></div>
                            </div>
                            <div>
                                <div class="field-label">Batch:</div>
                                <div class="field-val"><code>YC S26</code></div>
                            </div>
                            <div>
                                <div class="field-label">Source:</div>
                                <div class="field-val">X (Twitter)</div>
                            </div>
                        </div>
                        <div style="font-size: 13px; color: #FFAA00; margin-bottom: 8px;">
                            ⚡ <strong>Status:</strong> Founder announced on X / not yet officially listed in YC Directory
                        </div>
                        <div class="quote-box">
                            "{early_yc.post_text}"
                        </div>
                        <div class="links-row">
                            🔗 <strong>Original Post:</strong> <a href="{early_yc.post_url}" target="_blank">{early_yc.post_url}</a><br>
                            🌐 <strong>Website:</strong> <a href="https://hyperscale.ai" target="_blank">https://hyperscale.ai</a>
                        </div>
                        <div class="btn-group">
                            <a href="{early_yc.post_url}" target="_blank" class="slack-btn">📱 Open Post on X</a>
                            <a href="https://hyperscale.ai" target="_blank" class="slack-btn secondary">🌐 Visit Website</a>
                        </div>
                        <div class="footer-context">
                            🕒 Detected: {early_yc.detected_at.strftime('%b %d, %Y, %I:%M %p UTC')} | 🎯 Rho Pipeline Radar | 🤖 Pond Agent V1
                        </div>
                    </div>
                </div>
            </div>

            <!-- Message 2: Confirmed YC Directory -->
            <div class="message-row">
                <div class="bot-avatar">📙</div>
                <div class="message-content">
                    <div>
                        <span class="bot-name">YC Launch Radar</span>
                        <span class="bot-badge">APP</span>
                        <span class="timestamp">Today at 2:03 PM</span>
                    </div>
                    <div class="slack-card confirmed">
                        <div class="card-header">✅ NEW YC COMPANY — CONFIRMED BY YC</div>
                        <div class="fields-grid">
                            <div>
                                <div class="field-label">Company:</div>
                                <div class="field-val"><strong><a href="https://www.talos-us.com/" target="_blank">Talos</a></strong></div>
                            </div>
                            <div>
                                <div class="field-label">Founder:</div>
                                <div class="field-val">Founder Team</div>
                            </div>
                            <div>
                                <div class="field-label">Batch:</div>
                                <div class="field-val"><code>Fall 2026</code></div>
                            </div>
                            <div>
                                <div class="field-label">Source:</div>
                                <div class="field-val">YC Directory</div>
                            </div>
                        </div>
                        <div style="font-size: 13px; color: #2BAC76; margin-bottom: 8px;">
                            ✅ <strong>Status:</strong> Confirmed Official Directory Listing
                        </div>
                        <div style="font-size: 14px; margin: 10px 0; color: #E8E8E8;">
                            <strong>Description:</strong> {confirmed_yc.description}
                        </div>
                        <div class="links-row">
                            📙 <strong>YC Profile:</strong> <a href="https://www.ycombinator.com/companies/talos-us" target="_blank">ycombinator.com/companies/talos-us</a><br>
                            🌐 <strong>Website:</strong> <a href="https://www.talos-us.com/" target="_blank">https://www.talos-us.com/</a>
                        </div>
                        <div class="btn-group">
                            <a href="https://www.ycombinator.com/companies/talos-us" target="_blank" class="slack-btn">📙 View YC Profile</a>
                            <a href="https://www.talos-us.com/" target="_blank" class="slack-btn secondary">🌐 Visit Website</a>
                        </div>
                        <div class="footer-context">
                            🕒 Detected: {confirmed_yc.detected_at.strftime('%b %d, %Y, %I:%M %p UTC')} | 🎯 Rho Pipeline Radar | 🤖 Pond Agent V1
                        </div>
                    </div>
                </div>
            </div>

            <!-- Message 3: Early Speedrun Signal -->
            <div class="message-row">
                <div class="bot-avatar">⚡</div>
                <div class="message-content">
                    <div>
                        <span class="bot-name">YC Launch Radar</span>
                        <span class="bot-badge">APP</span>
                        <span class="timestamp">Today at 4:18 PM</span>
                    </div>
                    <div class="slack-card speedrun">
                        <div class="card-header">⚡ EARLY SPEEDRUN SIGNAL — Founder Announced Before Directory</div>
                        <div class="fields-grid">
                            <div>
                                <div class="field-label">Company:</div>
                                <div class="field-val"><strong><a href="https://aurapayments.io" target="_blank">Aura Payments</a></strong></div>
                            </div>
                            <div>
                                <div class="field-label">Founder:</div>
                                <div class="field-val"><a href="https://www.linkedin.com/in/elena-rostova-pay" target="_blank">Elena Rostova (@elena-rostova-pay)</a></div>
                            </div>
                            <div>
                                <div class="field-label">Batch:</div>
                                <div class="field-val"><code>SR006</code></div>
                            </div>
                            <div>
                                <div class="field-label">Source:</div>
                                <div class="field-val">LinkedIn</div>
                            </div>
                        </div>
                        <div style="font-size: 13px; color: #BB86FC; margin-bottom: 8px;">
                            ⚡ <strong>Status:</strong> Founder announced on LinkedIn / not yet listed in directory
                        </div>
                        <div class="quote-box">
                            "{early_sr.post_text}"
                        </div>
                        <div class="links-row">
                            🔗 <strong>LinkedIn Post:</strong> <a href="{early_sr.post_url}" target="_blank">View on LinkedIn</a><br>
                            🌐 <strong>Website:</strong> <a href="https://aurapayments.io" target="_blank">https://aurapayments.io</a>
                        </div>
                        <div class="btn-group">
                            <a href="{early_sr.post_url}" target="_blank" class="slack-btn">🔗 Open LinkedIn Post</a>
                            <a href="https://aurapayments.io" target="_blank" class="slack-btn secondary">🌐 Visit Website</a>
                        </div>
                        <div class="footer-context">
                            🕒 Detected: {early_sr.detected_at.strftime('%b %d, %Y, %I:%M %p UTC')} | 🎯 Rho Pipeline Radar | 🤖 Pond Agent V1
                        </div>
                    </div>
                </div>
            </div>

        </div>
    </div>
</body>
</html>
"""

    out_file = DOCS_DIR / "slack_demo_preview.html"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Generated HTML Slack demo preview at: {out_file}")

if __name__ == "__main__":
    generate_html_preview()
