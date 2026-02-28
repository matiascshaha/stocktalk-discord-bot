from dataclasses import dataclass


_RAW_REAL_MESSAGES = [
    (
        5,
        "stocktalkweekly",
        """
'The Greenland Basket' ( *This is a trading basket/living thematic trade. Positions can change at any time, and new positions will be added*)

New position: Pangea Logistics $PANL - 4% weight @ $7.23 avg on shares, also very small spot in $7.5C for May

Arctic ambitions (military or commercial) turn into revenue only when cargo, fuel, equipment, and ore can be moved in constrained seasons. PANL is a way to own Arctic-capable tonnage and execution.

Pangaea positions itself as an operator of a fleet that includes high ice-class vessels. *30% of their entire fleet is Ice Class 1A vessels.* This distinguishes them from other U.S. operators/competitors such as $CMBT, which has only 10% of its fleet as Ice Class, and that too Class 1C which are far less capable.

Ice Class 1A / 1B / 1C is basically a “how winter-hardened is this cargo ship for ice?” scale.

1A is the strongest of the three, 1C the lightest.

The rules test whether the ship can keep about 5 knots in a channel of broken ice of a certain thickness (thicker for 1A than 1B than 1C).

IA (≈ 1A): can operate in severe ice conditions, assisted if necessary by an icebreaker.

IB (≈ 1B): can operate in moderate ice conditions, assisted if necessary.

IC (≈ 1C): can operate in light ice conditions, assisted if necessary.

In its Q3 2025 earnings press release, management explicitly attributes results to “solid Arctic trade activity” and “robust utilization across our niche ice-class fleet,” and states that its niche ice-class model drove TCE rates ~10% above the market; the release also claims operation of “the world’s largest high ice-class dry bulk fleet of Panamax and post‑Panamax vessels.”

Structurally, as Arctic traffic increases (Arctic Council shipping trends) and as defense infrastructure in Greenland/High North sustains operations (Pituffik resupply reality), demand for scarce ice-capable logistics can command premiums.

$PANL is the “real economy” expression of Arctic buildout: bulk cargoes, project freight, seasonal route optimization, port/terminal interfaces. 

The *unique angle* on Pangea is that they are the only U.S. company to have built a "temporary port" in Greenland, the Moriusaq, Greenland “pop-up port” concept using a Pangaea-owned barge and a trial Arctic shipment to deliver "the northernmost dry bulk cargo *ever carried*" -- I find this to be *highly significant*.

The daily chart is also an absolute beauty, consolidating cleanly after a gap-up last November.

Stock is cheap trading at 10x forward P/E and 10x price to free cash flow, 0.8x sales growing top line +15% Y/Y (so far).
""",
        True,
        {"PANL"},
    ),
    (
        18,
        "stocktalkweekly",
        """
My current shipbuilding exposure is $HII which we've owned since early last year and has done very well for us (nearly doubled from low $200s to $400+). However, I want to increase my exposure to the shipbuilding and U.S. naval expansion phenomenon. 

There is a tremendous amount of policy focus here and I don't think it's going away for the next few years, especially with the launch of the Trump-class battleship. 

A shipbuilding focus means more emphasis on domestic maritime capacity. In order to expand port infrastructure (deepening and/or widening of ports) & build waterways/channels for large ships, dredging activity is required.  

Dredging is the underwater excavation and removal of sediment, silt, and debris from the bottom of water bodies like rivers, lakes, and harbors Warships have hard draft/underkeel-clearance constraints, and dredging is how you keep those access channels usable over time as sediment accumulates. It's difficult to find pure-play exposure to dredging, as there are not many options, but one I find compelling is **Great Lakes Dredge & Dock $GLDD**. 

GLDD benefits from the Foreign Dredge Act / Jones Act regime, which significantly restricts foreign-built/foreign-operated vessels from competing in U.S. dredging and coastwise trades. GLDD is building Acadia, described as the first and only Jones Act–qualified SRI vessel being constructed in the U.S.One of the risks is their offshore wind exposure (because Trump hates wind energy), but at only 7% of their total backlog, I think this risk is minimal/muted by the greater business. 

Where's the direct policy linkage?

Trump’s April 2025 executive order (“Restoring America’s Maritime Dominance”) is framed as a maritime-industrial-base program, not just shipyard grants.

- The EO directs an assessment of investment options to expand the “Maritime Industrial Base,” explicitly including port infrastructure and maritime port access, alongside shipbuilding and ship repair.

- More funding/priority for federal navigation O&M (maintenance dredging) through the HMTF pathway

- More political urgency for capital deepening/widening at strategic ports/shipyard approaches (general-fund + cost-share projects), because bigger commercial and naval vessels force the issue.

Added stock at $13.95 and some $12.5C for March at $1.75 avg just to add some juice. 4.5% weighting. 
""",
        True,
        {"GLDD"},
    ),
    (
        12,
        "stocktalkweekly",
        """
In my view, one of the biggest themes of this year will be Edge Compute & On-Device Inference. 

Currently, the only position in my portfolio that addresses this theme is $OSS, which is a core position. However, I would like to layer exposure here with a few more stocks.

One of those stocks is **Synaptics $SYNA** 

You should think of an “AI-capable device” as having three big layers:

1. Sensors & inputs (camera, microphones, touch, motion sensors)
2. Local compute (the chips that run the model and decide what’s happening)
3. Connectivity (Wi‑Fi/Bluetooth/etc. to talk to phones, routers, or other devices)

SYNA has products that map to (2) and (3) directly, and it markets itself as providing an integrated edge stack (compute + connectivity + multimodal support)

SYNA’s SL2610 family is described as integrating:

- General compute (Arm CPU cores)
- GPUs (NVIDIA or otherwise)
- An AI acceleration subsystem (Synaptics' Torq platform)

In layman’s terms: it’s designed so an OEM can build a device that sees/hears something, runs an AI model locally, and reacts, *without needing a datacenter or offsite server*

*GOOGLE PARTNERSHIP*

On January 2, 2025, Synaptics announced it was collaborating with Google on Edge AI for IoT to define “optimal implementation of multimodal processing for context-aware computing,” integrating Google’s MLIR-compliant ML core on Synaptics Astra hardware with open-source software/tools.

In October 2025, Synaptics announced the SL2610 line and stated that Torq delivers the first production deployment of Google’s RISC‑V-based Coral NPU with dynamic operator support, using an open-source IREE/MLIR compiler/runtime approach.

Google’s own developer documentation calls Synaptics its *first strategic silicon partner* for Coral NPU and says SL2610 features the first production implementation of Google’s open-source Coral NPU ML core

*THE 'ASTRA' PROGRAM*

Astra is not a single chip. It’s Synaptics’ AI‑native IoT compute platform that bundles together processor families (silicon), SL-series (high power MPUs built on Arm Cortex CPUs), SR-series (low-power MCUs) + software, hardware & connectivity. 

Astra is Synaptics effort to sell the “whole kit” that makes an IoT device smart on its own: a processor that can run AI locally, the software tools to deploy models, and the dev hardware + wireless pieces to get a product built and shipped faster.

Astra launched in April 2024, but in October 2025 they updated Astra to the next generation *purpose-built* for edge AI workloads:

- Synaptics announced the Astra SL2600 Series, launching with the SL2610 product line, positioned for multimodal Edge AI and a wide set of IoT endpoints (appliances, automation, charging infrastructure, healthcare, retail POS/scanners, robotics/UAVs, etc.) -- this provides very robust *multi-theme exposure*

- SL2610 is explicitly tied to the Torq Edge AI platform and Google’s open Coral NPU

The thesis behind on-device compute is that: *some inference leaves the data center and moves to endpoints* Astra is a direct lever to this idea, because Astra is literally designed for endpoints that:

- generate raw data (camera/mic/sensor)
- need real-time responses
- can’t depend on network reliability

In my opinion, the company trades at a very reasonable valuation of 21x free cash flow, 21 trailing P/E, 15 forward P/E, 3x sales ($1.1B vs. $3B mkt cap) with a PEG ratio of 0.82 (which is below 1, implying the stock is undervalued). Management is guiding for 25-30% CAGR in their IOT business over the next 4 years, which is massive growth in the key segment considering this type of undemanding valuation.

I've added $SYNA shares at $85.78, 6% weight. The options are illiquid currently, but I may try to work into some $85C across multiple strikes if the spreads tighten. Earnings between Feb 4-9. If the earnings go well and corroborate my thesis, then there is a chance this will be designated as a core position. <@&933985135391547462>
...
""",
        True,
        {"SYNA"},
    ),
    # MUST RETURN []
    (
        5,
        "stocktalkweekly",
        """
PORTFOLIO UPDATE -15 POSITIONS

88:12 - EQUITY:OPTIONS RATIO

LISTING FORMAT: % WEIGHTING - $TICKER (OPTIONS) - COMMON SHARES COST BASIS

Core positions will be marked with an asterisk *

POWER GRID / BATTERIES

20-21%: $ENS* (Shares + $115C Mar '26) - $116.63

4-5%: $PLPC* - $192.16

U.S. SEMICONDUCTOR SUPPLY CHAIN

17-18%: $AMKR* (Shares + $25C Mar '26, $30C Jun '26) - $24.35

EDGE/ON-DEVICE COMPUTE

9-10%: $OSS* - $4.71

6-7%: $SYNA (Shares + $85C Mar '26) - $85.78 

DATACENTER

8-9%: VIAV* (Shares + $14C Mar '26) - $13.84

4-5%: $NBIS* - $23.92

2-3%: $THR - $36.59

NUCLEAR

7-8%: $LEU* - $96.94

AEROSPACE & DEFENSE

6-7%: $HII - $236.40

4-5%: $GLDD (Shares + $12.5C Mar '26) - $13.95

3-4%: $KTOS* (Shares + $35C & $40C Jan '27) - $22.34

LEGACY POSITIONS

2-3%: $HOOD* - $19.74

2-3%: $TSLA* - $19.38

2-3%: $AMZN* (Shares + $250C Jan '28) - $88.93

Cash: -3.2%

All positions are alerted live in this journal. These weekly portfolio updates are for the sake of completeness.

Core positions generally indicate either: A) deep cost-basis advantages B) high-weighting C) high-conviction, or all three. Core positions are NOT subject to trims unless explicitly stated in this journal.

Many positions (but not all) have accompanying options exposure across multiple dates & strikes. The positions with options leverage (if they are liquid) are noted. If options are not noted, the position is either entirely in common stock, or the owned options are illiquid.

If you're interested in when an alert went out, please search "from:stocktalkweekly $TICKER" and you will be able to find the original post. You can also tag me in the questions channel as always.

Remember that just because the weighting of a given position changes, it does not mean stock was bought or sold. Relative outperformance or underperformance of a position can lead to a shift in weighting.

If you're a new member and you missed the initial alerts, explore the portfolio and examine the charts on your own for an ideal entry. I share *exactly what I do*, the rest is up to you.

Search: "from:stocktalkweekly PORTFOLIO UPDATE" to see previous portfolio updates. <@&933985135391547462>
""",
        False,
        set()),
]


FROZEN_COMMON_SHARES_MESSAGE = "New position: Apple $AAPL - 3% weight @ $190 avg on shares"

FROZEN_OPTIONS_MESSAGE = (
    "Added AAPL $200C for March 2026, small speculative options position only."
)

FROZEN_MIXED_MESSAGE = (
    "Added TSLA common shares and a small TSLA call option starter for follow-through."
)

FROZEN_NO_ACTION_MESSAGE = (
    "Portfolio update only: no new positions or recommendations in this post."
)

FROZEN_WEIGHTED_MESSAGE = "New position: NVDA - 12.5% weighting target for this setup."

FROZEN_DOLLAR_AMOUNT_MESSAGE = "New position: MSFT with standard default dollar sizing."


IRDM_OPTIONS_REAL_MESSAGE = """
I have been trying to re-enter Iridium (ticker I-R-D-M) in a tactical manner that is not too capital intensive, so I have been scaling into some $22.5C for July 17 at $3.35 avg over the past several days. Very conservative sizing, 1.5% weighting, but just the calls. You can take shares instead if you don't want to deal with the volatility. I like how the daily structure is confirming support at the 200-day and I think since their earnings, my original thesis on BVLOS and PNT has been further validated (see my original $IRDM thesis from December here: stock-talk-portfolio) @Stock Talk Weekly - Alerts
""".strip()


MITK_POSITION_REAL_MESSAGE = """
One of the ideas I have been strongly drawn to this year is the notion that AI is bringing in a new age of identity/fraud/verification threats that we have never seen before, and that companies with technologies that are built to enforce the trust ecosystem will see real momentum as a consequence of this. Deepfakes, spoofs, voice-imitation, and data-scraping have compromised modern liveness and identity standards across multiple industries. $YOU just posted a fantastic quarter with their Clear1 enterprise identity solutions program, confirming momentum in this space. However, there is another name that reported recently in this space that I have been watching closely, and I now feel there is enough broader data supporting the trend to initiate a position.

It will be just the third small-cap in the portfolio joining $OSS & $PANL (+100% and +30% from our entries respectively).

That name is Mitek (ticker M-I-T-K).

Mitek's Q1 FY26 investor presentation frames their core investment thesis clearly: fraud is entering a new phase where AI-generated synthetic identities and deepfakes are outpacing legacy controls, and enterprises increasingly need accurate, multi-signal decisioning across onboarding, authentication, and transaction risk, rather than stitching together fragmented point tools from multiple vendors. Mitek's claim to win this shift is that its Verified Identity Platform (MiVIP) unifies identity verification, authentication, liveness/deepfake detection, and advanced fraud analytics in a single workflow, while still operating a mission-critical check platform at scale. In layman's terms: Mitek is positioning itself as an all-in-one reality check for digital interactions-proving a person and their credentials are real even when attackers can generate convincing fakes.

Fraud & Identity Solutions is now the growth engine and is overtaking the legacy Check Verification business. In Q1 FY26, total revenue was about $44M (+19% YoY), with Fraud & Identity Solutions at ~$25M (+30% YoY) versus Check Verification at ~$19M (+6% YoY), meaning Fraud & Identity is larger than Check in the quarter. On a trailing-twelve-month basis, the deck shows Fraud & Identity at $96M vs. Check at $91M, i.e., 51% vs. 49% of LTM revenue, explicitly crossing the majority threshold. Nonetheless, it is worth noting that the Check Verification business process 1.2B transaction each year, and has upwards of 99% market share, giving it strong pricing power if volumes wane.

Mitek's biometrics stack (from ID R&D, now part of Mitek) includes IDLive Face (passive face liveness to detect presentation and injection attacks), IDLive Doc (document liveness), and IDLive Voice (anti-spoofing voice liveness, it also added voice-clone detection that can score the likelihood speech was generated by cloning technology from only a few seconds of audio), and its site explicitly categorizes deepfake attack and injection attack as fraud types it addresses. It's not just matching your selfie to your ID, it's trying to prove you're a live human and not a replay, a mask, or an AI-injected video feed.

The distribution/customer access angle is one of Mitek's most underappreciated differentiators versus many identity point-solution vendors. The investor presentation states its technology supports more than one billion mobile deposits annually, which implies it is already deeply embedded in high-volume banking workflows; and outside the deck, Mitek has publicly stated that it is trusted by thousands of organizations and that the majority of North American financial institutions rely on its mobile check deposit solutions. That legacy footprint isn't just old revenue, it is a distribution rail: it provides executive relationships, procurement paths, and operational trust inside highly regulated customers who are now being forced to upgrade defenses against AI-driven fraud. @Stock Talk Weekly - Alerts
""".strip()


ITRI_COMMON_REAL_MESSAGE = """
The goal of my Power Grid basket (currently comprising of $ENS and $PLPC), is to play the modernization of the U.S. electric grid. One stock I've been monitoring for the past few quarters is Itron. After their most recent earnings report earlier this week, I feel comfortable adding this name to the Power Grid basket.

Itron specializes in Advanced Metering Infrastructure (AMI). Itron is an end-to-end grid edge technology provider to utilities. The Networked Solutions segment makes up 2/3rd of the company's revenue, which implies that most of their customers are seeking & trusting Itron for end-to-end solutions, which means: communicating endpoints (smart meters, modules, endpoints, sensors) + network infrastructure + headend management + application software.

In layman's terms, they make the smart meter and sensors that sit at homes, businesses, and on parts of the grid. These devices measure what's happening (electric/gas/water usage, power quality events, outages) and provide the communication system that lets those meters/sensors talk back to the utility automatically. A modern grid requires modern metering infrastructure.

Utilities use their products to detect outages faster and see where they are, find leaks/theft/abnormal usage patterns, forecast demand and manage peak load, integrate rooftop solar, batteries, and EV charging more safely, and run billing and customer portals with more accurate, near-real-time data. Newer grid means more new metering infrastructure and more grid usage means higher importance for end-to-end benefits like these.

As far as exposure purity goes Itron identifies themselves as the #1 metering company in North America with 60% share of electric AMI and that 75% of all power in the US touches Itron technology -- which is a bold statement. William Blair's 3rd party analyst estimates 2/3rd of their revenue is tied to electricity. This constitutes more than enough direct exposure to the grid.

Like many stocks in my portfolio, Itron is heavily weighted to North America exposure - 81% of their revenue comes from North America. While some may view this as a geographical concentration risk, I view it conversely as exactly the type of exposure I am seeking, as I'm looking to play grid modernization in the U.S. specifically.

Itron's peers in electric smart metering include much larger, more expensive comps like $HUBB & $XYL and much smaller, yet still more expensive and unprofitable, comps like $LAND. Water metering comps include names like $BMI, which is a good business, but is 90% water and has no electric grid exposure.

It is important to note the company is not yet showing overall growth in the near-term, but I believe the +23% growth in ARR is providing significantly higher visibility, and the rapidly growing Outcomes segment also posted +24% Y/Y growth, and has now overtaken the Device Solutions segment to become the 2nd largest business segment. The Outcomes segment is their value-added services layer, which includes data management and grid planning. The company just hit their 2027 targets on gross margin & free cash flow conversion (37% & 12%) 2 years ahead of schedule (posted 38% GM and 16.2% FCF)

I believe Itron stock is very reasonably valued, and thus I believe there is opportunity for multiple expansion here irrespective of acceleration in growth, especially based on the thematic relevance. Stock trades at a trailing P/E of 15, forward P/E of 14, 13 EV/EBITDA, 11.8x free cash flow, and less than 2x sales.

Important to keep in mind that technically speaking the stock is below its 200-day moving average, so you should expect price action to be volatile and frustrating at times. This is typical for stocks that have not yet reclaimed their 200-day. Nonetheless, I like the risk-reward at these levels.

I've opened a new position in Itron (ticker: I-T-R-I) this morning with a 5.5% weighting, all common stock at $99.10 average. <@&933985135391547462>
""".strip()


@dataclass(frozen=True)
class MessageFixture:
    scenario_id: str
    author: str
    text: str
    should_pick: bool
    expected_tickers: frozenset[str]
    reference_id: int | None = None
    family: str = "general"


REAL_PIPELINE_MESSAGE_KEYS = (
    "real_panl_greenland_basket",
    "real_gldd_shipbuilding_dredge",
    "real_syna_edge_compute",
    "real_portfolio_update_no_action",
)

FROZEN_MESSAGE_KEYS = (
    "frozen_common_shares",
    "frozen_options_only",
    "frozen_mixed_commons_options",
    "frozen_no_action",
    "frozen_weighted",
    "frozen_dollar_amount",
)

AI_PROMPT_MESSAGE_KEYS = (
    "real_irdm_options",
    "real_mitk_common_position",
    "real_itri_weighted_common",
)


def _build_fixture(
    scenario_id: str,
    author: str,
    text: str,
    should_pick: bool,
    expected_tickers: set[str] | frozenset[str],
    reference_id: int | None,
    family: str,
) -> MessageFixture:
    return MessageFixture(
        scenario_id=scenario_id,
        author=author,
        text=text,
        should_pick=should_pick,
        expected_tickers=frozenset(expected_tickers),
        reference_id=reference_id,
        family=family,
    )


if len(REAL_PIPELINE_MESSAGE_KEYS) != len(_RAW_REAL_MESSAGES):
    raise ValueError("REAL_PIPELINE_MESSAGE_KEYS count must match _RAW_REAL_MESSAGES")


MESSAGE_FIXTURES: dict[str, MessageFixture] = {}

for scenario_id, raw_case in zip(REAL_PIPELINE_MESSAGE_KEYS, _RAW_REAL_MESSAGES):
    msg_id, author, text, should_pick, tickers = raw_case
    MESSAGE_FIXTURES[scenario_id] = _build_fixture(
        scenario_id=scenario_id,
        author=author,
        text=text,
        should_pick=should_pick,
        expected_tickers=tickers,
        reference_id=msg_id,
        family="real_pipeline",
    )


MESSAGE_FIXTURES.update(
    {
        "frozen_common_shares": _build_fixture(
            scenario_id="frozen_common_shares",
            author="stocktalkweekly",
            text=FROZEN_COMMON_SHARES_MESSAGE,
            should_pick=True,
            expected_tickers={"AAPL"},
            reference_id=None,
            family="frozen",
        ),
        "frozen_options_only": _build_fixture(
            scenario_id="frozen_options_only",
            author="stocktalkweekly",
            text=FROZEN_OPTIONS_MESSAGE,
            should_pick=True,
            expected_tickers={"AAPL"},
            reference_id=None,
            family="frozen",
        ),
        "frozen_mixed_commons_options": _build_fixture(
            scenario_id="frozen_mixed_commons_options",
            author="stocktalkweekly",
            text=FROZEN_MIXED_MESSAGE,
            should_pick=True,
            expected_tickers={"TSLA"},
            reference_id=None,
            family="frozen",
        ),
        "frozen_no_action": _build_fixture(
            scenario_id="frozen_no_action",
            author="stocktalkweekly",
            text=FROZEN_NO_ACTION_MESSAGE,
            should_pick=False,
            expected_tickers=set(),
            reference_id=None,
            family="frozen",
        ),
        "frozen_weighted": _build_fixture(
            scenario_id="frozen_weighted",
            author="stocktalkweekly",
            text=FROZEN_WEIGHTED_MESSAGE,
            should_pick=True,
            expected_tickers={"NVDA"},
            reference_id=None,
            family="frozen",
        ),
        "frozen_dollar_amount": _build_fixture(
            scenario_id="frozen_dollar_amount",
            author="stocktalkweekly",
            text=FROZEN_DOLLAR_AMOUNT_MESSAGE,
            should_pick=True,
            expected_tickers={"MSFT"},
            reference_id=None,
            family="frozen",
        ),
        "real_irdm_options": _build_fixture(
            scenario_id="real_irdm_options",
            author="stocktalkweekly",
            text=IRDM_OPTIONS_REAL_MESSAGE,
            should_pick=True,
            expected_tickers={"IRDM"},
            reference_id=None,
            family="ai_prompt_real",
        ),
        "real_mitk_common_position": _build_fixture(
            scenario_id="real_mitk_common_position",
            author="stocktalkweekly",
            text=MITK_POSITION_REAL_MESSAGE,
            should_pick=True,
            expected_tickers={"MITK"},
            reference_id=None,
            family="ai_prompt_real",
        ),
        "real_itri_weighted_common": _build_fixture(
            scenario_id="real_itri_weighted_common",
            author="stocktalkweekly",
            text=ITRI_COMMON_REAL_MESSAGE,
            should_pick=True,
            expected_tickers={"ITRI"},
            reference_id=None,
            family="ai_prompt_real",
        ),
    }
)


REAL_PIPELINE_CASES = tuple(MESSAGE_FIXTURES[key] for key in REAL_PIPELINE_MESSAGE_KEYS)
