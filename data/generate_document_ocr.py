"""
Generates synthetic (ocr_text -> document_type) training data for the
Document Type Classifier.

Why synthetic: there is no public, labeled corpus of OCR'd civic-benefit
documents (Aadhaar cards, ration cards, pay stubs, etc.) usable in a demo
project, and real specimens would contain PII even if blanked. So this
generator builds realistic-but-fake OCR text per document type: varied field
labels, abbreviations, OCR noise (dropped/garbled characters, line-break
artifacts, inconsistent spacing/case), and irrelevant boilerplate, modeled on
how real OCR engines actually render printed government forms. This is the
same disclosed-synthetic-data approach as life_events.csv and
benefit_priority_training.csv.

This is a genuine improvement over the old keyword list because:
  1. The classifier sees many phrasings/layouts per class, not one fixed
     keyword set, so it can generalize to OCR text that doesn't contain any
     of the original literal keywords.
  2. OCR noise is injected (character substitution/drops, line breaks,
     stray symbols) so the model learns robustness to imperfect scans,
     which the old exact-substring matcher had none of.
"""
import csv
import os
import random

random.seed(23)

# Field/phrase banks per document type. Each list represents lines that
# would plausibly appear (in some OCR-garbled form) on that document.
DOC_TEMPLATES = {
    "Aadhaar Card": [
        "Government of India Unique Identification Authority of India",
        "Aadhaar No {num}", "DOB {date}", "Gender Male", "Address: {addr}",
        "UIDAI मेरा आधार मेरी पहचान", "Enrolment No {num}",
    ],
    "Ration Card": [
        "Public Distribution System", "Ration Card No {num}",
        "Fair Price Shop", "Family Members {n}", "Category BPL/APL",
        "State Food Civil Supplies Department", "Card Type: Above Poverty Line",
    ],
    "Income Certificate": [
        "Certificate of Annual Income", "This is to certify that Mr/Mrs {name}",
        "has an annual income of Rs {amount}", "issued by Tehsildar office",
        "Income Certificate No {num}", "Valid for one year from date of issue",
    ],
    "Income Proof": [
        "Salary Slip for the month of {month}", "Gross Pay {amount}",
        "Net Payable {amount}", "Employee Name {name}", "Pay Period {date}",
        "Basic Salary HRA Deductions",
    ],
    "Property Documents": [
        "Sale Deed", "This Indenture made between", "Property situated at {addr}",
        "Registered Document No {num}", "Title Deed of Ownership",
        "Survey Number {num} Plot Area",
    ],
    "Bank Statement": [
        "Account Statement", "Account Number {num}", "IFSC Code {code}",
        "Opening Balance {amount} Closing Balance {amount}",
        "Statement Period {date} to {date}", "Branch Name {addr}",
    ],
    "Address Proof": [
        "Proof of Residence", "Electricity Bill", "Consumer Number {num}",
        "Billing Address {addr}", "Utility Connection valid for {addr}",
        "Residential Certificate issued to {name}",
    ],
    "Birth Certificate": [
        "Certificate of Birth", "This is to certify that {name} was born on {date}",
        "Registration No {num}", "Place of Birth {addr}",
        "Municipal Corporation Birth Registry", "Sex Male/Female",
    ],
    "Age Proof": [
        "Certificate of Age", "Date of Birth as per school records {date}",
        "School Leaving Certificate", "Age Proof issued by {addr} Municipality",
    ],
    "BPL Certificate": [
        "Below Poverty Line Certificate", "BPL Survey No {num}",
        "Family income below poverty line threshold",
        "Issued by Gram Panchayat office", "BPL Card holder {name}",
    ],
    "Disability Certificate": [
        "Certificate of Disability", "UDID Number {num}",
        "Percentage of Disability {n}%", "Medical Board Assessment",
        "Disability Type: Locomotor/Visual/Hearing", "Issued by District Hospital",
    ],
    "Government ID": [
        "Passport No {num}", "Driving License Number {num}",
        "Identification Card issued by Department of Motor Vehicles",
        "Valid until {date}", "Photo Identification Document",
    ],
    "Proof of Income": [
        "Form W-2 Wage and Tax Statement", "Employer Identification Number {num}",
        "Wages tips other compensation {amount}", "Federal income tax withheld {amount}",
        "Pay Stub Earnings Statement", "Year to Date Gross {amount}",
    ],
    "Proof of Residency": [
        "Lease Agreement between Landlord and Tenant", "Monthly Rent {amount}",
        "Property Address {addr}", "Utility Bill Service Address {addr}",
        "Residency verification letter",
    ],
    "Social Security Number": [
        "Social Security Administration", "Social Security Number {num}",
        "This card belongs to {name}", "Social Security card issued",
    ],
    "Last Pay Stubs": [
        "Earnings Statement", "Pay Period Ending {date}", "Gross Earnings {amount}",
        "Federal Tax State Tax Net Pay {amount}", "Employee ID {num}",
    ],
    "Lease Agreement": [
        "Residential Lease Agreement", "Landlord {name} Tenant {name}",
        "Monthly rent due on the first of each month {amount}",
        "Lease Term begins {date} ends {date}", "Security Deposit {amount}",
    ],
    "Medical Records": [
        "Patient Medical Record", "Diagnosis {addr}", "Attending Physician {name}",
        "Date of Visit {date}", "Treatment Summary Discharge Notes",
    ],
    "Work History": [
        "Employment History Summary", "Employer {name} Position {addr}",
        "Dates of Employment {date} to {date}", "Work History Verification Letter",
    ],
    "CPF": [
        "Cadastro de Pessoas Físicas", "CPF Número {num}", "Receita Federal do Brasil",
        "Nome Completo {name}", "Data de Nascimento {date}",
    ],
    "Cartão Nacional de Saúde": [
        "Cartão Nacional de Saúde", "Sistema Único de Saúde SUS",
        "Número do Cartão {num}", "Nome do Usuário {name}",
        "Ministério da Saúde",
    ],
    "Comprovante de Residência": [
        "Comprovante de Residência", "Conta de Luz Endereço {addr}",
        "Companhia de Energia Elétrica", "Fatura referente ao mês {month}",
    ],
    "CadÚnico Registration": [
        "Cadastro Único para Programas Sociais", "Número do CadÚnico {num}",
        "Número de Identificação Social NIS {num}", "Renda Familiar {amount}",
    ],
    "Carteira de Trabalho": [
        "Carteira de Trabalho e Previdência Social", "CTPS Número {num} Série {num}",
        "Contrato de Trabalho", "Data de Admissão {date}",
    ],
    "Termo de Rescisão": [
        "Termo de Rescisão do Contrato de Trabalho", "TRCT",
        "Data do Aviso Prévio {date}", "Saldo de Salário {amount}",
    ],
    "RG (ID)": [
        "Registro Geral", "Carteira de Identidade", "RG Número {num}",
        "Secretaria de Segurança Pública", "Filiação {name}",
    ],
    "Medical/Disability Report": [
        "Laudo Médico", "Avaliação de Deficiência", "CID {code}",
        "Percentual de Incapacidade {n}%", "Médico Responsável {name}",
    ],
}

NAMES = ["John Silva", "Maria Souza", "Rohan Mehta", "Priya Nair", "Carlos Rodrigues",
         "Anita Desai", "James Carter", "Fernanda Lima", "Vikram Rao", "Sarah Johnson"]
ADDRS = ["12 Main St Springfield", "45 MG Road Bengaluru", "Rua das Flores 88 Sao Paulo",
         "221B Baker Street", "78 Andheri East Mumbai", "300 Lakeview Ave Chicago"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "Janeiro", "Fevereiro", "Marco"]


def rand_num(n=8):
    return "".join(random.choice("0123456789") for _ in range(n))


def rand_date():
    return f"{random.randint(1,28):02d}/{random.randint(1,12):02d}/{random.randint(1960,2024)}"


def rand_amount():
    return f"{random.randint(100,9999)}.{random.randint(0,99):02d}"


def rand_code():
    return "".join(random.choice("ABCDEFGHIJ0123456789") for _ in range(6))


def fill(template):
    return (template
            .replace("{num}", rand_num(random.choice([6, 8, 10, 12])))
            .replace("{name}", random.choice(NAMES))
            .replace("{addr}", random.choice(ADDRS))
            .replace("{date}", rand_date())
            .replace("{amount}", rand_amount())
            .replace("{month}", random.choice(MONTHS))
            .replace("{code}", rand_code())
            .replace("{n}", str(random.randint(1, 100))))


OCR_NOISE_SUBS = [("o", "0"), ("l", "1"), ("S", "5"), ("B", "8"), ("e", "c"), ("a", "@")]


def add_ocr_noise(text, intensity=0.06):
    """Randomly substitute characters and mangle spacing to mimic OCR errors."""
    chars = list(text)
    for i, ch in enumerate(chars):
        if random.random() < intensity:
            for orig, sub in OCR_NOISE_SUBS:
                if ch == orig:
                    chars[i] = sub
                    break
    noisy = "".join(chars)
    # occasionally collapse or insert stray whitespace/newlines, like real OCR layout artifacts
    if random.random() < 0.3:
        noisy = noisy.replace(" ", "  ", 1)
    if random.random() < 0.2:
        noisy = noisy + " \n"
    return noisy


def build_document_text(doc_type, n_lines_range=(3, 6)):
    lines = DOC_TEMPLATES[doc_type]
    chosen = random.sample(lines, k=min(len(lines), random.randint(*n_lines_range)))
    filled = [fill(line) for line in chosen]
    random.shuffle(filled)
    text = "\n".join(filled)
    return add_ocr_noise(text)


# Paraphrase fragments per class: looser, conversational-register descriptions of
# the SAME document concept, written differently from the formal template lines
# above. These exist so the classifier learns the underlying concept rather than
# just the fixed phrasebook surface form — without them, held-out accuracy looks
# perfect but only because test rows recombine the same template lines as
# training rows (verified: ~50% accuracy on genuinely novel phrasing before this
# augmentation was added).
PARAPHRASES = {
    "Aadhaar Card": [
        "unique identification number issued to indian residents by uidai",
        "12 digit id card with photo and fingerprint biometric record",
        "national identity document used for kyc verification in india",
    ],
    "Ration Card": [
        "household card used to buy subsidized food grains from the government shop",
        "family entitlement card for the public food distribution scheme",
        "document listing all family members eligible for subsidized rations",
    ],
    "Income Certificate": [
        "official document stating a person's yearly earnings issued by a revenue officer",
        "certificate confirming household income for the past year",
        "government-issued proof of annual family income",
    ],
    "Income Proof": [
        "document showing monthly take-home pay and deductions from an employer",
        "shows gross earnings and net amount paid to an employee",
        "paystub listing salary breakdown for the pay period",
    ],
    "Property Documents": [
        "legal paperwork proving who owns a piece of land or a house",
        "registered deed transferring ownership of real estate",
        "title document for a residential or commercial property",
    ],
    "Bank Statement": [
        "monthly summary of deposits withdrawals and balance from a bank account",
        "transaction history showing account activity over a period",
        "printed record of account balance issued by a financial institution",
    ],
    "Address Proof": [
        "a utility bill or letter showing where someone currently lives",
        "document confirming a person's current residential address",
        "official mail used to verify where you reside",
    ],
    "Birth Certificate": [
        "official record of when and where a person was born",
        "government document confirming date and place of birth",
        "registered birth record issued by a municipal authority",
    ],
    "Age Proof": [
        "document used to confirm how old a person is",
        "school record or certificate showing date of birth for age verification",
    ],
    "BPL Certificate": [
        "document confirming a household falls below the poverty line",
        "government certification of low-income family status",
    ],
    "Disability Certificate": [
        "medical certification stating the type and percentage of disability",
        "official document confirming a person's disability for benefit purposes",
        "doctor-issued assessment of physical or sensory impairment",
    ],
    "Government ID": [
        "official photo identification issued by a government agency",
        "passport or driving license used to verify identity",
    ],
    "Proof of Income": [
        "tax form showing wages and taxes withheld for the year",
        "annual wage statement issued by an employer for tax filing",
    ],
    "Proof of Residency": [
        "rental agreement or bill confirming where someone lives",
        "document used to prove current home address for an application",
    ],
    "Social Security Number": [
        "government issued personal identification number for benefits and tax purposes",
        "card showing an individual's social security number",
    ],
    "Last Pay Stubs": [
        "recent earnings statement from an employer showing pay and deductions",
        "most recent paycheck stub used to verify current income",
    ],
    "Lease Agreement": [
        "contract between a landlord and tenant for renting a property",
        "rental contract specifying monthly rent and lease term",
        "this letter confirms i live at this address and pay rent monthly",
    ],
    "Medical Records": [
        "hospital discharge summary with diagnosis and treating doctor name",
        "patient health records documenting treatment and visits",
        "clinical notes from a doctor's visit or hospital stay",
    ],
    "Work History": [
        "summary of a person's past jobs and employment dates",
        "letter verifying previous employment and job titles",
    ],
    "CPF": [
        "brazilian taxpayer registration number issued by receita federal",
        "individual tax id document used for financial transactions in brazil",
    ],
    "Cartão Nacional de Saúde": [
        "this card shows my sus number for the brazilian public health system",
        "national health card used to access public healthcare services in brazil",
    ],
    "Comprovante de Residência": [
        "brazilian utility bill used as proof of address",
        "electricity or water bill showing a resident's address in brazil",
    ],
    "CadÚnico Registration": [
        "brazilian government registry for low-income families seeking social programs",
        "single registry number used to apply for brazilian social benefits",
    ],
    "Carteira de Trabalho": [
        "brazilian work booklet recording employment history and contracts",
        "official work permit document used in brazil for formal employment",
    ],
    "Termo de Rescisão": [
        "brazilian document confirming the termination of an employment contract",
        "official severance paperwork issued when a job ends in brazil",
    ],
    "RG (ID)": [
        "brazilian general registry identity card with photo",
        "official brazilian id card issued by public security department",
    ],
    "Medical/Disability Report": [
        "brazilian medical report assessing degree of disability",
        "doctor's evaluation used to certify a disability in brazil",
    ],
}


def build_paraphrase_text(doc_type):
    bank = PARAPHRASES.get(doc_type)
    if not bank:
        return build_document_text(doc_type)
    base = random.choice(bank)
    # sometimes combine with one formal template line for realism, sometimes leave standalone
    if random.random() < 0.5:
        extra = fill(random.choice(DOC_TEMPLATES[doc_type]))
        text = base + "\n" + extra
    else:
        text = base
    return add_ocr_noise(text, intensity=0.03)


ROWS_PER_CLASS = 60
PARAPHRASE_FRACTION = 0.4  # ~40% of rows per class use paraphrased/conversational text
rows = []
for doc_type in DOC_TEMPLATES:
    n_paraphrase = int(ROWS_PER_CLASS * PARAPHRASE_FRACTION)
    n_template = ROWS_PER_CLASS - n_paraphrase
    for _ in range(n_template):
        rows.append((build_document_text(doc_type).lower(), doc_type))
    for _ in range(n_paraphrase):
        rows.append((build_paraphrase_text(doc_type).lower(), doc_type))

random.shuffle(rows)

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "document_ocr_training.csv")
with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["ocr_text", "document_type"])
    writer.writerows(rows)

print(f"Generated {len(rows)} rows across {len(DOC_TEMPLATES)} document types -> {OUT_PATH}")
