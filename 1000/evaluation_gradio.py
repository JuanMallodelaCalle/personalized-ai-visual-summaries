import gradio as gr
import os
import random
import json
import pandas as pd

# paths
DATA_PATH = "C:/Users/Juan/Desktop/TFM/1000/gradio"
EVAL_PATH = "C:/Users/Juan/Desktop/TFM/1000/evaluation"

os.makedirs(EVAL_PATH, exist_ok=True)

json_files = [f for f in os.listdir(DATA_PATH) if f.endswith(".json")]

# profile images (ending in _A.png or _B.png)
all_profile_images = [f for f in os.listdir(DATA_PATH) if f.endswith(".png") and ("_A.png" in f or "_B.png" in f)]

# profile appearance options (classification)
profile_appearance_opts = [
    "Sub-Saharan African (Nigeria, Kenya, Ethiopia, South Africa, etc.)",
    "North African & Middle Eastern (MENA) (Egypt, Morocco, Saudi Arabia, Iran, etc.)",
    "European (Southern / Mediterranean) (Italy, Spain, Greece, Portugal, etc.)",
    "European (Northern & Eastern) (Germany, Poland, Sweden, Russia, etc.)",
    "South Asian (India, Pakistan, Sri Lanka, Nepal, etc.)",
    "East Asian (China, Korea, Japan, Mongolia, etc.)",
    "Southeast Asian (Vietnam, Thailand, Philippines, Indonesia, etc.)",
    "North American (USA, Canada, Greenland, etc.)",
    "Central & South American (Mexico, Peru, Bolivia, Chile, etc.)",
    "Oceanian / Pacific Islander (Fiji, Samoa, Papua New Guinea, Hawaii, etc.)",
]

# list of countries (registration)
COUNTRIES = [
    "Albania","Algeria","Andorra","Angola","Argentina","Armenia","Australia","Austria","Bangladesh","Belgium","Bolivia","Brazil","Bulgaria",
    "Canada","Chile","China","Colombia","Croatia","Cuba","Cyprus","Czech Republic","Denmark","Dominican Republic","Ecuador","Egypt","El Salvador","Estonia",
    "Ethiopia","Finland","France","Germany","Greece","Guatemala","Honduras","Hungary","Iceland","India","Indonesia","Iran","Iraq","Ireland","Israel","Italy",
    "Jamaica","Japan","Jordan","Kazakhstan","Kenya","Latvia","Lebanon","Lithuania","Luxembourg","Malaysia","Malta","Mexico","Moldova","Monaco","Mongolia",
    "Morocco","Netherlands","New Zealand","Nicaragua","Nigeria","North Macedonia","Norway","Pakistan","Panama","Paraguay","Peru","Philippines","Poland",
    "Portugal","Qatar","Romania","Russia","Saudi Arabia","Serbia","Singapore","Slovakia","Slovenia","South Africa","South Korea","Spain","Sri Lanka","Sweden",
    "Switzerland","Syria","Taiwan","Thailand","Tunisia","Turkey","Ukraine","United Arab Emirates","United Kingdom","United States","Uruguay","Venezuela",
    "Vietnam","Yemen","Zambia","Zimbabwe"
]

AGE_GROUPS = ["18-29", "30-39", "40-49", "50+"]
GENDER_CHOICES = ["Man", "Woman", "Other", "Prefer not to say"]

# per-profile estimation (age/sex)
PROFILE_AGE_GROUPS = ["4–12", "13–17", "18–29", "30–39", "40–49", "50–59", "60+"]
PROFILE_SEX_CHOICES = ["Man", "Woman", "Other / Can't tell"]

MAX_TURNS = 30  # maximum number of dialogue turns + images

eval_params = ["Realism", "Coherence with dialogue", "Consistency of characters"]

custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap');

/* Montserrat font */
body, html { font-family: 'Montserrat', sans-serif !important; }

/* text elements */
.gr-text, .gr-textbox, .gr-number, .gr-markdown, label, input, textarea {
  font-family: 'Montserrat', sans-serif !important;
}

/* clean boxes and shadows */
.gr-box, .gr-panel, .gr-group {
  background-color: transparent !important;
  box-shadow: none !important;
  border: none !important;
}

/* buttons */
button {
  font-family: 'Montserrat', sans-serif !important;
  border-radius: 8px !important;
  padding: 10px 16px !important;
  transition: background-color 0.2s ease;
  border: none !important;
}

/* inputs */
input, textarea {
  border: 1px solid #ccc !important;
  border-radius: 6px !important;
  padding: 6px 10px !important;
}

/* images without box */
.gr-image, .gr-image > div {
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  transition: none !important;
  padding: 0 !important;
  margin: 0 !important;
}
.gr-image img {
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  margin: 0 !important;
}
.gr-image:hover { background-color: transparent !important; cursor: default !important; }

/* fullscreen/download icons */
svg { transition: fill 0.2s ease; }

/* spacing */
.gr-block { margin-top: 8px !important; margin-bottom: 8px !important; }

/* ==== Dropdowns always downwards (not floating, not covering images) ==== */

/* normal container, not relative or floating */
.gr-dropdown .wrap {
  position: static !important;
}

/* menu behaves as normal block below the field */
.gr-dropdown .wrap [role="listbox"] {
  position: static !important;          /* stop being absolute */
  display: block !important;
  margin-top: 6px !important;
  max-height: 260px !important;
  overflow-y: auto !important;

  /* visual style */
  background: #ffffff !important;
  border: 1px solid #ddd !important;
  border-radius: 6px !important;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;

  /* ensure it pushes layout down */
  top: auto !important;
  bottom: auto !important;
  transform: none !important;
  z-index: auto !important;
}

/* ensure no overflow limits cut it off */
.gradio-container, .gr-block, .gr-group, .gr-column, .gr-row {
  overflow: visible !important;
}

/* sections */
.section-title {
  font-weight: 700;
  font-size: 50px;
  margin: 10px 0 6px 0;
  padding: 6px 10px;
  border-left: 4px solid #999;
  background: #f7f7f7;
}

/* label per dialogue image */
.image-turn-label {
  margin-top: 14px;
  padding: 6px 10px;
  border: 1px dashed #bbb;
  border-radius: 8px;
  font-size: 24px;
  background: #fafafa;
}

/* status box colors */
.status-ok {
  margin-top: 12px;
  padding: 10px 14px;
  border-radius: 8px;
  background: #e8f7ec;
  border: 1px solid #9bd3aa;
  color: #245c33;
  font-weight: 600;
}
.status-err {
  margin-top: 12px;
  padding: 10px 14px;
  border-radius: 8px;
  background: #fdeaea;
  border: 1px solid #f1a6a6;
  color: #7c2323;
  font-weight: 600;
}

/* ===== Instructions: card with padding ===== */
.instructions-card {
  background: #e6f0fa;              /* light blue */
  padding: 28px 30px;               /* <-- internal space */
  border-radius: 12px;
  border: 1px solid #d6e4f6;
  line-height: 1.6;
}
.instructions-card h1, 
.instructions-card h2, 
.instructions-card h3 {
  margin-top: 0.2rem;
}

.section-big {
    font-size: 50px !important;
}

/* more space after evaluating each dialogue image */
.after-image {
  margin-bottom: 40px !important;  /* separates image from dialogue continuation */
}

/* some air between sliders too */
.gr-slider {
  margin-bottom: 6px !important;
}

"""

instructions_md = """
# Welcome to the Profiles and Dialogue Evaluation Tool

## About this Project
This tool is part of my **Master's Thesis (TFM)**, focused on exploring how **visual representations of dialogues** can improve their interpretability.  
The project generates **coherent image sequences** from dialogues, based on character profiles and conversation turns.  
By enriching personalities with **traits and visual attributes**, the aim is to create **multimodal dialogues** where characters remain visually consistent across turns.

The ultimate goal is to evaluate how **images** can complement **textual dialogues**, making them more **immersive and accessible**.

#### Note: The dialogues used in this project are sourced from two established open datasets — PersonaChat and ComperDial — which provide the textual basis for each conversation. Only the images have been generated synthetically for research and evaluation purposes.

<br>

## Ethical Guidelines & Consent
- **You must be 18 or older** to participate.  
- Do **not share personal information** (names, addresses, contact details, etc.).  
- Your **nickname** should be anonymous — do not use your real name or anything that identifies you.  
- All responses will be treated confidentially and used only for research purposes.

By continuing, you confirm that you understand and agree to these guidelines.

<br>

## What You Will Evaluate
You will be asked to evaluate **two types of images**:

1. **Profile Images (A and B):**  
   - For each character profile, you will select the **most likely ethnic/appearance group** (you can choose more than one, with a maximum of three) from a predefined list.  
   - ⚠️ **Important:** these categories are **not identities**, but **perceptual labels** used in computer vision research.  
   - They are based on international standards and datasets and aim to provide a **multicultural but manageable division** of human appearances.  
   - The division balances recognizability (e.g., East Asian, Sub-Saharan African) with granularity (e.g., separating Southern vs. Northern European).    
   - Also estimate the **age group** and **sex** of each profile image.
   - This classification is used **only for evaluating visual outputs** and **not** as a judgment of real identity.  
   - You may also **report issues** in the image (e.g., additional text, visual artifacts, extra fingers, inconsistent reflections, impossible poses).

2. **Dialogue Images (sequence generated during the conversation):**  
   - For each generated image, you will evaluate it on:
     - **Realism** - Does the image look realistic and believable?  
     - **Coherence with dialogue** - Does the image match the content of the conversation?  
     - **Consistency of characters** - Do the characters remain visually consistent across turns? If a dialogue image does not visibly show either of the two main characters, please evaluate the “consistency of characters” based on the surrounding environment or contextual clues (e.g., objects, locations, or mood that align with the dialogue). If no relevant cues are visible, you may assign a neutral score (10) to indicate that no inconsistency is perceived.
   - You may also **report problems** (e.g., artifacts, hallucinations, body part errors) in the dedicated textbox below each image.  

⚠️ **Important rules for evaluation:**  
- All dialogue images must be rated (>0-10) in every category before submission.  
- Profile appearances, age group, and sex (A and B) must also be selected before submission.  
- Reports are **optional** but encouraged when you notice any clear issue. 

<br>

## Final Note
Thank you very much for participating in this research.
Your feedback will directly contribute to the improvement of multimodal AI systems and the success of this thesis project.
"""

# -------- UI helpers ----------
def show_registration():
    return gr.update(visible=True)

def complete_registration(nickname, age_group, gender, nationality):
    if not nickname or nickname.strip() == "":
        return "Please enter a valid nickname.", gr.update(visible=True), gr.update(visible=False)
    if age_group not in AGE_GROUPS:
        return "Please select an age group (18+).", gr.update(visible=True), gr.update(visible=False)
    if gender not in GENDER_CHOICES:
        return "Please select a gender option.", gr.update(visible=True), gr.update(visible=False)
    if nationality not in COUNTRIES:
        return "Please select your nationality from the list.", gr.update(visible=True), gr.update(visible=False)

    # OK: hide instructions/registration and show evaluation
    return "Registration completed. You can start the evaluation.", gr.update(visible=False), gr.update(visible=True)

# status HTML
def status_html(msg: str, kind: str = "error"):
    cls = "status-ok" if kind == "ok" else "status-err"
    return f"<div class='{cls}'>{msg}</div>"

# helper to not reset on validation failure and only show status (bottom)
def hold_everything_and_show_status(msg: str, kind: str = "error"):
    """
    Returns a list of outputs that:
    - updates only the status with `msg` and visible=True (as html with color)
    - keeps all other outputs exactly the same (empty gr.update())
    - keeps buttons as they are (also empty gr.update())
    """
    base_core = 15
    per_turn = 4 + len(eval_params)  # markdown + label + image + report + sliders(3)
    core_count = base_core + MAX_TURNS * per_turn + 4  # +4 hidden
    unchanged_core = [gr.update() for _ in range(core_count)]
    unchanged_buttons = [gr.update(), gr.update()]  # start_btn, submit_btn unchanged
    return [gr.update(value=status_html(msg, kind), visible=True)] + unchanged_core + unchanged_buttons


def enforce_max3(selected):
    """
    Limits multi-selection to a maximum of 3 items.
    """
    if not selected:
        return []
    return selected[:3]


# ---------- Evaluation ----------
def start_evaluation(nickname, age_group, seen_ids):
    # if not registered
    if not nickname or nickname.strip() == "" or age_group not in AGE_GROUPS:
        outputs = [gr.update(value=status_html("Please register first (nickname + age group).", "error"), visible=True)]
        outputs += ["", gr.update(visible=False),  # dialogue_id, title profiles
                    gr.update(value=None, visible=False), gr.update(value=None, visible=False),  # imgs A/B
                    gr.update(visible=False),           # accordionA OFF
                    gr.update(value=[], visible=False),   # appearance A
                    gr.update(value=None, visible=False), # age A
                    gr.update(value=None, visible=False), # sex A
                    gr.update(value="", visible=False),   # report A
                    gr.update(visible=False),           # accordionB OFF
                    gr.update(value=[], visible=False),   # appearance B
                    gr.update(value=None, visible=False), # age B
                    gr.update(value=None, visible=False), # sex B
                    gr.update(value="", visible=False),   # report B
                    gr.update(visible=False)]             # title dialogue
        for _ in range(MAX_TURNS):
            outputs += [gr.update(value=None, visible=False),  # markdown
                        gr.update(value=None, visible=False),  # image label
                        gr.update(value=None, visible=False)]  # image
            for _ in eval_params:
                outputs.append(gr.update(value=0, visible=False))
            outputs.append(gr.update(value="", visible=False))  # report textbox
        outputs += [gr.update(value="", visible=False), gr.update(value="", visible=False),
                    gr.update(value="", visible=False), gr.update(value="0", visible=False)]
        outputs += [gr.update(visible=True), gr.update(visible=False)]
        return outputs + [gr.update(value=seen_ids)]

    # find a json whose dialogue_id is NOT in seen_ids
    remaining_files = []
    for f in json_files:
        path = os.path.join(DATA_PATH, f)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                d = json.load(fh)
            if d.get("dialogue_id") and d["dialogue_id"] not in (seen_ids or []):
                remaining_files.append((f, d["dialogue_id"]))
        except Exception:
            continue

    if not remaining_files:
        msg = "🎉 All available dialogues have been evaluated in this session. Restart the app or clear the session to start over."
        return [gr.update(value=status_html(msg, "ok"), visible=True)] \
               + reset_outputs_core() \
               + [gr.update(visible=True), gr.update(visible=False)] \
               + [gr.update(value=seen_ids)]

    # choose one at random from remaining
    chosen_file, dialogue_id = random.choice(remaining_files)
    dialogue_path = os.path.join(DATA_PATH, chosen_file)
    with open(dialogue_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    dialogue_id = data["dialogue_id"]
    profile_A = os.path.join(DATA_PATH, f"{dialogue_id}_A.png")
    profile_B = os.path.join(DATA_PATH, f"{dialogue_id}_B.png")

    outputs = [gr.update(value="", visible=False)]
    outputs.append(dialogue_id)                 # dialogue_id_out
    outputs.append(gr.update(visible=True))     # section_profiles_title ON
    outputs.append(gr.update(value=profile_A if os.path.isfile(profile_A) else None, visible=True))  # A
    outputs.append(gr.update(value=profile_B if os.path.isfile(profile_B) else None, visible=True))  # B

    # profile A controls
    outputs.append(gr.update(visible=True))   # accordionA ON
    outputs.append(gr.update(value=[], visible=True))       # appearance A
    outputs.append(gr.update(value=None, visible=True))     # age A
    outputs.append(gr.update(value=None, visible=True))     # sex A
    outputs.append(gr.update(value="", visible=True))       # report A

    # profile B controls
    outputs.append(gr.update(visible=True))   # accordionB ON
    outputs.append(gr.update(value=[], visible=True))       # appearance B
    outputs.append(gr.update(value=None, visible=True))     # age B
    outputs.append(gr.update(value=None, visible=True))     # sex B
    outputs.append(gr.update(value="", visible=True))       # report B

    outputs.append(gr.update(visible=True))     # section_dialogue_title ON

    # iterate dialogue
    img_slots = []
    img_counter = 0
    slot_index = 0  # 0..MAX_TURNS-1

    for turn in data["dialogue"]:
        if "persona_id" in turn:
            speaker = "A" if "_A" in turn["persona_id"] else "B"
            text_key = [k for k in turn.keys() if k.startswith("text_")][0]
            text = turn[text_key]
            justify = "flex-start" if speaker == "A" else "flex-end"
            bg_color = "#dcf8c6" if speaker == "A" else "#cce5ff"
            text_align = "left" if speaker == "A" else "right"
            md_text = f"""
            <div style='display: flex; justify-content: {justify};'>
                <div style='background-color: {bg_color}; padding: 12px 18px;
                            border-radius: 15px; margin: 6px 0; max-width: 75%;
                            font-size: 18px; color: #000000 !important; text-align: {text_align};'>
                    <span style='color: #000000 !important; font-weight: 600;'>{speaker}:</span> {text}
                </div>
            </div>
            """
            outputs.append(gr.update(value=md_text, visible=True))   # markdown ON
            outputs.append(gr.update(value=None, visible=False))     # image label OFF
            outputs.append(gr.update(value=None, visible=False))     # image OFF
            for _ in eval_params:
                outputs.append(gr.update(value=0, visible=False))
            outputs.append(gr.update(value="", visible=False))       # report OFF
            slot_index += 1

        elif "image_id" in turn:
            img_path = os.path.join(DATA_PATH, f"{turn['image_id']}.png")
            if os.path.isfile(img_path):
                img_counter += 1
                img_slots.append(slot_index)
                outputs.append(gr.update(value=None, visible=False))  # markdown OFF
                outputs.append(gr.update(value=f"<div class='image-turn-label'>Image #{img_counter}</div>", visible=True))  # label ON
                outputs.append(gr.update(value=img_path, visible=True))  # image ON
                for _ in eval_params:
                    outputs.append(gr.update(value=0, visible=True))
                outputs.append(gr.update(value="", visible=True))         # report textbox ON
            else:
                outputs.append(gr.update(value=None, visible=False))
                outputs.append(gr.update(value=None, visible=False))
                outputs.append(gr.update(value=None, visible=False))
                for _ in eval_params:
                    outputs.append(gr.update(value=0, visible=False))
                outputs.append(gr.update(value="", visible=False))
            slot_index += 1

        else:
            outputs.append(gr.update(value=None, visible=False))
            outputs.append(gr.update(value=None, visible=False))
            outputs.append(gr.update(value=None, visible=False))
            for _ in eval_params:
                outputs.append(gr.update(value=0, visible=False))
            outputs.append(gr.update(value="", visible=False))
            slot_index += 1

    # fill up to MAX_TURNS
    used_slots = slot_index
    for _ in range(MAX_TURNS - used_slots):
        outputs.append(gr.update(value=None, visible=False))  # markdown
        outputs.append(gr.update(value=None, visible=False))  # label
        outputs.append(gr.update(value=None, visible=False))  # image
        for _ in eval_params:
            outputs.append(gr.update(value=0, visible=False))  # sliders
        outputs.append(gr.update(value="", visible=False))     # report

    # hidden fields
    outputs.append(gr.update(value=profile_A, visible=False))              # profile_A_path_hidden
    outputs.append(gr.update(value=profile_B, visible=False))              # profile_B_path_hidden
    outputs.append(gr.update(value=",".join(map(str, img_slots)), visible=False))  # image_slots_hidden
    outputs.append(gr.update(value=str(img_counter), visible=False))              # image_count_hidden

    new_seen = (seen_ids or []) + [dialogue_id]
    return outputs + [
        gr.update(visible=False),  # Start OFF
        gr.update(visible=True),   # Submit ON
        gr.update(value=new_seen)  # seen_ids_state
    ]


def reset_outputs_core():
    """
    Returns ONLY the 'core' block (without the first status and without buttons),
    Reset to show only Start Evaluation.
    """
    core = []
    core += ["", gr.update(visible=False),
             gr.update(value=None, visible=False), gr.update(value=None, visible=False),
             gr.update(visible=False),                    # accordionA OFF
             gr.update(value=[], visible=False), gr.update(value=None, visible=False), gr.update(value=None, visible=False), gr.update(value="", visible=False),
             gr.update(visible=False),                    # accordionB OFF
             gr.update(value=[], visible=False), gr.update(value=None, visible=False), gr.update(value=None, visible=False), gr.update(value="", visible=False),
             gr.update(visible=False)]
    for _ in range(MAX_TURNS):
        core += [gr.update(value=None, visible=False),  # markdown
                 gr.update(value=None, visible=False),  # image label
                 gr.update(value=None, visible=False)]  # image
        for _ in eval_params:
            core.append(gr.update(value=0, visible=False))
        core.append(gr.update(value="", visible=False))  # report textbox
    core += [gr.update(value="", visible=False), gr.update(value="", visible=False),
             gr.update(value="", visible=False), gr.update(value="0", visible=False)]
    return core


def submit_evaluation(nickname, age_group, gender, participant_nat, dialogue_id,
                      appearanceA, ageA, sexA, appearanceB, ageB, sexB,
                      profA_path, profB_path, image_slots_csv, image_count_str,
                      reportA, reportB, seen_ids, *tail):
    """
    tail = [report_texts (MAX_TURNS)] + [sliders (3*MAX_TURNS)]
    """
    report_text_vals = list(tail[:MAX_TURNS])
    sliders_flat = list(tail[MAX_TURNS:])

    # basic registration checks
    if not nickname or age_group not in AGE_GROUPS or gender not in GENDER_CHOICES or participant_nat not in COUNTRIES:
        return hold_everything_and_show_status("Please complete registration first.", "error") + [gr.update(value=seen_ids)]

    # appearance A and B (multi): at least 1
    if not appearanceA or len(appearanceA) == 0 or not appearanceB or len(appearanceB) == 0:
        return hold_everything_and_show_status("Please select at least one appearance group for both profiles (A and B).", "error") + [gr.update(value=seen_ids)]
    # max 3 appearances per profile
    if len(appearanceA) > 3 or len(appearanceB) > 3:
        return hold_everything_and_show_status(
            "Please select at most three appearance groups per profile (A and B).", "error"
        ) + [gr.update(value=seen_ids)]
    # age and sex per profile mandatory
    if ageA not in PROFILE_AGE_GROUPS or sexA not in PROFILE_SEX_CHOICES:
        return hold_everything_and_show_status("Please select age group and sex for Profile A.", "error") + [gr.update(value=seen_ids)]
    if ageB not in PROFILE_AGE_GROUPS or sexB not in PROFILE_SEX_CHOICES:
        return hold_everything_and_show_status("Please select age group and sex for Profile B.", "error") + [gr.update(value=seen_ids)]

    # parsing image slots used in this dialogue
    img_slots = []
    if image_slots_csv and image_slots_csv.strip():
        try:
            img_slots = [int(x) for x in image_slots_csv.split(",") if x.strip() != ""]
        except:
            img_slots = []
    try:
        img_count = int(image_count_str)
    except:
        img_count = 0

    # recover sliders arrays (by slot index)
    n_images_slots = MAX_TURNS
    realism_vals = sliders_flat[0:n_images_slots]
    coherence_vals = sliders_flat[n_images_slots:2*n_images_slots]
    consistency_vals = sliders_flat[2*n_images_slots:3*n_images_slots]

    # check that ALL shown images were evaluated (>= 0.5)
    missing = []
    for idx_order, slot in enumerate(img_slots, start=1):
        rv = float(realism_vals[slot] or 0)
        cv = float(coherence_vals[slot] or 0)
        sv = float(consistency_vals[slot] or 0)
        if rv < 0.5 or cv < 0.5 or sv < 0.5:
            missing.append(f"Image #{idx_order}")
    if missing:
        msg = "Please rate all images before submitting. Missing: " + ", ".join(missing)
        return hold_everything_and_show_status(msg, "error") + [gr.update(value=seen_ids)]

    # build dialogue rows
    rows_dialogue = []
    for idx_order, slot in enumerate(img_slots, start=1):
        rv = float(realism_vals[slot] or 0)
        cv = float(coherence_vals[slot] or 0)
        sv = float(consistency_vals[slot] or 0)
        report_txt = (report_text_vals[slot] or "").strip()
        rows_dialogue.append({
            "User": nickname,
            "Age group": age_group,
            "Gender": gender,
            "Nationality (participant)": participant_nat,
            "Dialogue ID": dialogue_id,
            "Image": idx_order,
            "Realism": rv,
            "Coherence with dialogue": cv,
            "Consistency of characters": sv,
            "Report": report_txt
        })

    # save A/B profiles
    imgA_name = os.path.basename(profA_path) if profA_path else "Unknown"
    imgB_name = os.path.basename(profB_path) if profB_path else "Unknown"
    rows_profiles = [
        {
            "User": nickname, "Age group": age_group, "Gender": gender, "Nationality (participant)": participant_nat,
            "Dialogue ID": dialogue_id, "Profile": "A", "Profile Image": imgA_name,
            "Selected appearance(s)": "; ".join(appearanceA or []),
            "Estimated age (profile)": ageA,
            "Estimated sex (profile)": sexA,
            "Report": (reportA or "").strip()
        },
        {
            "User": nickname, "Age group": age_group, "Gender": gender, "Nationality (participant)": participant_nat,
            "Dialogue ID": dialogue_id, "Profile": "B", "Profile Image": imgB_name,
            "Selected appearance(s)": "; ".join(appearanceB or []),
            "Estimated age (profile)": ageB,
            "Estimated sex (profile)": sexB,
            "Report": (reportB or "").strip()
        },
    ]

    # write Excels
    filename_dialogue = os.path.join(EVAL_PATH, "evaluation_results.xlsx")
    if rows_dialogue:
        df_new_d = pd.DataFrame(rows_dialogue)
        if os.path.isfile(filename_dialogue):
            df_existing_d = pd.read_excel(filename_dialogue)
            df_all_d = pd.concat([df_existing_d, df_new_d], ignore_index=True)
        else:
            df_all_d = df_new_d
        df_all_d.to_excel(filename_dialogue, index=False)

    filename_profiles = os.path.join(EVAL_PATH, "profile_appearance_selections.xlsx")
    df_new_p = pd.DataFrame(rows_profiles)
    if os.path.isfile(filename_profiles):
        df_existing_p = pd.read_excel(filename_profiles)
        df_all_p = pd.concat([df_existing_p, df_new_p], ignore_index=True)
    else:
        df_all_p = df_new_p
    df_all_p.to_excel(filename_profiles, index=False)

    # message + reset to "Start only" state
    thanks = gr.update(value=status_html("✅ Thank you for participating! You can close this window or start a new evaluation!", "ok"),
                       visible=True)
    return [thanks] + reset_outputs_core() + [gr.update(visible=True), gr.update(visible=False), gr.update(value=seen_ids)]

# ---------- UI ----------
with gr.Blocks(theme=gr.themes.Soft(), css=custom_css) as demo:

    # ======= Instructions + registration =======
    with gr.Group(visible=True) as instructions_group:
        gr.Markdown(instructions_md, elem_classes=["instructions-card"])
        proceed_btn = gr.Button("Proceed to Registration")

        with gr.Group(visible=False) as registration_group:
            gr.Markdown("### &nbsp;&nbsp;&nbsp;Registration", elem_classes=["registration-title"])
            with gr.Row():
                nickname = gr.Textbox(label="Nickname (anonymous)",
                                      placeholder="Choose a non-identifying nickname",
                                      interactive=True, scale=1)
                age_group = gr.Dropdown(choices=AGE_GROUPS, label="Age group (18+ only)",
                                        interactive=True, value=None, scale=1)
            with gr.Row():
                gender = gr.Dropdown(choices=GENDER_CHOICES, label="Gender",
                                     interactive=True, value=None, scale=1)
                nationality = gr.Dropdown(choices=COUNTRIES, label="Nationality",
                                          interactive=True, filterable=True, value=None, scale=1)
            register_btn = gr.Button("Complete Registration")
            registration_status = gr.Text(label="Status", show_label=False)  # sin etiqueta

        proceed_btn.click(fn=show_registration, inputs=None, outputs=registration_group)

    # ======= Unified evaluation =======
    with gr.Group(visible=False) as evaluation_group:
        dialogue_id_out = gr.Textbox(label="Dialogue ID", interactive=False, visible=False)

        section_profiles_title = gr.Markdown("**Profile images**", visible=False, elem_classes=["section-title"])
        with gr.Row():
            with gr.Column():
                profile_A_img = gr.Image(label="Profile A", interactive=False, height=350, width=350, visible=False)
                accordionA = gr.Accordion("Profile A: appearance (max 3)", open=False, visible=False)
                with accordionA:
                    appearanceA = gr.CheckboxGroup(
                        choices=profile_appearance_opts,
                        label=None,
                        value=[],
                        visible=True
                    )
                ageA = gr.Dropdown(choices=PROFILE_AGE_GROUPS, label="Profile A: estimated age", value=None, visible=False)
                sexA = gr.Dropdown(choices=PROFILE_SEX_CHOICES, label="Profile A: estimated sex", value=None, visible=False)
                reportA_text = gr.Textbox(label="Report issues (optional)", lines=2, visible=False)
            with gr.Column():
                profile_B_img = gr.Image(label="Profile B", interactive=False, height=350, width=350, visible=False)
                accordionB = gr.Accordion("Profile B: appearance (max 3)", open=False, visible=False)
                with accordionB:
                    appearanceB = gr.CheckboxGroup(
                        choices=profile_appearance_opts,
                        label=None,
                        value=[],
                        visible=True
                    )
                ageB = gr.Dropdown(choices=PROFILE_AGE_GROUPS, label="Profile B: estimated age", value=None, visible=False)
                sexB = gr.Dropdown(choices=PROFILE_SEX_CHOICES, label="Profile B: estimated sex", value=None, visible=False)
                reportB_text = gr.Textbox(label="Report issues (optional)", lines=2, visible=False)

        appearanceA.change(fn=enforce_max3, inputs=appearanceA, outputs=appearanceA)
        appearanceB.change(fn=enforce_max3, inputs=appearanceB, outputs=appearanceB)

        section_dialogue_title = gr.Markdown("**Dialogue**", visible=False, elem_classes=["section-title"])

        # hidden fields to save real paths of a/b and image slots
        profile_A_path_hidden = gr.Textbox(visible=False)
        profile_B_path_hidden = gr.Textbox(visible=False)
        image_slots_hidden = gr.Textbox(visible=False)
        image_count_hidden = gr.Textbox(visible=False)

        # dialogue + sliders + report (all hidden at start)
        turn_markdowns = []
        image_labels = []
        turn_images = []
        report_texts = []
        sliders = {p: [] for p in eval_params}
        for i in range(MAX_TURNS):
            turn_markdowns.append(gr.Markdown(visible=False))
            image_labels.append(gr.Markdown(visible=False))
            turn_images.append(gr.Image(visible=False, interactive=False, height=480))
            for p in eval_params:
                sliders[p].append(gr.Slider(minimum=0, maximum=10, step=0.5, label=p, visible=False))
            report_texts.append(gr.Textbox(label="Report issues (optional)", lines=2, visible=False, elem_classes=["after-image"]))

        seen_ids_state = gr.State([])  # list of dialogue_id seen in this session

        # buttons
        with gr.Row():
            start_btn = gr.Button("Start Evaluation", visible=True)
            submit_btn = gr.Button("Submit Evaluation", visible=False)

        status_dialogue = gr.HTML(visible=False)

        # ===== outputs_core (without status) in this order =====
        outputs_core_components = [
            dialogue_id_out,             # 0
            section_profiles_title,      # 1
            profile_A_img,               # 2
            profile_B_img,               # 3

            accordionA,
            appearanceA,                 # 4
            ageA,                        # 5
            sexA,                        # 6
            reportA_text,                # 7

            accordionB,
            appearanceB,                 # 8
            ageB,                        # 9
            sexB,                        # 10
            reportB_text,                # 11

            section_dialogue_title       # 12
        ]
        for i in range(MAX_TURNS):
            outputs_core_components.append(turn_markdowns[i])   # text
            outputs_core_components.append(image_labels[i])     # image label
            outputs_core_components.append(turn_images[i])      # image
            for p in eval_params:
                outputs_core_components.append(sliders[p][i])   # sliders
            outputs_core_components.append(report_texts[i])     # report textbox per image

        outputs_core_components.extend([
            profile_A_path_hidden, profile_B_path_hidden,
            image_slots_hidden, image_count_hidden
        ])

        # events
        start_btn.click(
            fn=start_evaluation,
            inputs=[nickname, age_group, seen_ids_state],
            outputs=[status_dialogue] + outputs_core_components + [start_btn, submit_btn, seen_ids_state]
        )

        submit_btn.click(
            fn=submit_evaluation,
            inputs=[nickname, age_group, gender, nationality, dialogue_id_out,
                    appearanceA, ageA, sexA, appearanceB, ageB, sexB,
                    profile_A_path_hidden, profile_B_path_hidden,
                    image_slots_hidden, image_count_hidden,
                    reportA_text, reportB_text,
                    seen_ids_state] +
                   report_texts +
                   [slider for p in eval_params for slider in sliders[p]],
            outputs=[status_dialogue] + outputs_core_components + [start_btn, submit_btn, seen_ids_state]
        )

    # complete registration: pass to evaluation
    register_btn.click(
        fn=complete_registration,
        inputs=[nickname, age_group, gender, nationality],
        outputs=[registration_status, instructions_group, evaluation_group]
    )

demo.launch(share=False)
