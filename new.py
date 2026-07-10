from urllib.parse import urlparse

def get_invalid_urls(url_list):
    invalid_urls = []
    
    for item in url_list:
        # Parse the string
        parsed = urlparse(item.strip())
        
        # A valid URL must have both a scheme (like http/https) and a netloc (domain)
        is_valid = all([parsed.scheme, parsed.netloc])
        
        if not is_valid:
            invalid_urls.append(item)
            
    return invalid_urls

# Example Data
bunch_of_urls = [
"https://www.astrazeneca.in/content/dam/az-in/II-2024/Leave-and-Holiday-Policy.pdf",
"https://www.upl-ltd.com/images/people/downloads/Leave-Policy-India.pdf",
"https://dmec.org/wp-content/uploads/DMEC-Sample-Policy_Leave-of-Absence.pdf",
"https://familyfriendlytampabay.org/wp-content/uploads/2018/02/SampleLeavePoliciesandPointersWAPELRA-89351.pdf",
"https://www.ctas.tennessee.edu/eli/sample-policy-vacationannual-leave",
"http://dopt.gov.in/sites/default/files/Revised_AIS_Rule_Vol_I_Rule_03.pdf",
"https://www.cgspublicationindia.com/pdf/Leave/CCS(Leave)%20Rules%201972%20Updated%2019.09.2022.pdf",
"https://nitrr.ac.in/downloads/forms/admin/LEAVE%20RULES.pdf",
"https://www.scribd.com/document/411572123/Leave-Rules",
"https://cag.gov.in/uploads/media/ag-au-jh-office-manual-Chapter-9-20200706121919.pdf",
"https://www.workstream.us/policy-templates/compensation-policy",
"https://gusto.com/resources/hiring/templates/compensation-policy-template",
"https://www.shrm.org/topics-tools/tools/policies/performance-and-salary-review-policy",
"https://www.prothman.com/JobFiles/3029/Compensation%20Policy.pdf",
"https://www.qobra.co/blog/compensation-policy-examples",
"https://www.insperity.com/blog/compensation-policy/",
"https://www.higginbotham.com/blog/total-compensation-package-examples/",
"https://www.adp.com/resources/articles-and-insights/articles/c/compensation-plan.aspx",
"https://www.icl-group.com/wp-content/uploads/2024/10/ICL-Compensation-Policy-for-Office-Holders-2024-2027.pdf",
"https://cms6.revize.com/revize/highlandparkil/government/city_departments/city_manager_s_office/human_resources/docs/Compensation%20Policy%20Effective%20010119%20-%20Final.pdf",
"https://hexaware.com/wp-content/uploads/2024/02/i_POSH_Policy-1.pdf",
"https://www.bharatbiotech.com/corporate-governance/posh-policy.pdf",
"https://www.seic.com/ent/posh-policy",
"https://www.bata.com/in/posh-policy.html",
"https://www.nestle.in/sites/g/files/pydnoa451/files/investors/documents/nestl%C3%A9-india-posh.pdf",
"https://www.tataconsumer.com/sites/g/files/gfwrlq316/files/2023-05/Prevention%20of%20Sexual%20Harassment%20Policy.pdf",
"https://www.tata.com/content/dam/tata/pdf/tata-industries/POSH-TataIndustries-Policy.pdf",
"https://www.hul.co.in/files/origin/84b27036a3d850b91dc1e261fcf3c2a7852c4f0f.pdf/POSH_Policy_WYSNFQ%20(2).pdf",
"https://ttlwebassets.tatatechnologies.com/app/uploads/2023/03/Global-Policy-on-POSH.pdf",
"https://www.tatachemicals.com/upload/content_pdf/POSH_Policy.pdf",
"https://smartgivers.org/wp-content/uploads/2019/04/Sample-Expense-Reimbursement-Policy.docx",
"https://vitl.net/wp-content/uploads/2023/09/Employee-Expense-Reimbursement-Policy-2023-APPROVED-External-Use.pdf",
"https://www.radcommons.org/research/files/Partners-Policy-and-Procedures-for-Employee-Business-Expenses.pdf",
"https://www.hazelhawkins.com/documents/content/Travel-Business-Expense-Reimbursement-Policy.pdf",
"https://www.hrh.ca/wp-content/uploads/2019/02/Expense-Reimbursement-Policy-Approved-Dec-6-2018.pdf",
"https://resources.workable.com/employee-expense-company-policy",
"https://lattice.com/templates/employee-expense-reimbursement-policy",
"https://www.shrm.org/topics-tools/tools/policies/expense-reimbursement-policy",
"https://www.rippling.com/blog/expense-policy",
"https://navan.com/blog/free-expense-policy-template-sample-download",
"https://ir.aboutamazon.com/corporate-governance/documents-and-charters/code-of-business-conduct-and-ethics/default.aspx",
"https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/microsoft/mscle/documents/presentations/Trust_Code_2022_en-us_2023_0509.pdf",
"https://www08.wellsfargomedia.com/assets/pdf/about/corporate/code-of-conduct.pdf",
"https://www.relx.com/~/media/Files/R/RELX-Group/documents/investors/corporate-governance/code-of-ethics/code-of-ethics-english.pdf",
"https://www.appliedmaterials.com/content/dam/site/company/about/doc/corporate-governance/sbc.pdf.coredownload.inline.pdf",
"https://www.rangeresources.com/about-us/corporate-governance/code-of-business-conduct-ethics/",
"https://lifetimebrands.gcs-web.com/static-files/54611606-98ff-459d-ae1d-4494d68dc4d1",
"https://www.sec.gov/Archives/edgar/data/789073/000119312507093855/dex141.html",
"https://www.apple.com/compliance/pdfs/Business-Conduct-Policy.pdf",
"https://abc.xyz/investor/board-and-governance/google-code-of-conduct/"
]

# Run the filter and print results
print("Items that are NOT valid URLs:")
for invalid in get_invalid_urls(bunch_of_urls):
    print(invalid)
