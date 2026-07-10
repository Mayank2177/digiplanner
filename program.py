import re

def format_urls(text):
    # Split the input text into individual lines
    lines = text.strip().split('\n')
    
    formatted_lines = []
    for line in lines:
        # Remove whitespace and clean up internal spaces (like 'www. abc.pdf' to 'www.abc.pdf')
        cleaned_url = re.sub(r'\s+', '', line)
        
        # Wrap the cleaned URL in double quotes if the line is not empty
        if cleaned_url:
            formatted_lines.append(f'"{cleaned_url}",')
            
    return formatted_lines

# Example input with multi-line URL links
url_paragraph = """
https://www.opm.gov/policy-data-oversight/pay-leave/leave-administration/
https://www.calhr.ca.gov/about-calhr/divisions-programs/personnel-management/leave-benefits/
https://www.mass.gov/guides/absence-and-leave-policies
https://scmd.sc.gov/sites/scmd/files/Documents/Website/Policies/104/E24-104.05%20-%20Leave%20Without%20Pay%20-%2024%20April%202024.pdf
https://cdn.kingcounty.gov/-/media/king-county/depts/dhr/documents/benefits/leaves/leave-guide.pdf
https://doc.arkansas.gov/wp-content/uploads/Employee-Leave-AD.pdf
https://policy.ucop.edu/doc/4010406
https://www.utsystem.edu/sites/policy-library/policies/hop-331-leave-policy
https://hr.unc.edu/wp-content/uploads/sites/1483/2025/12/leave-request-hr-rep-guide.pdf
https://www.clemson.edu/human-resources/policies-and-procedures/61.html
https://www.ctas.tennessee.edu/eli/sample-policy-vacationannual-leave
https://spiresafety.com.au/resources/leave-policy/
https://signalhrm.com/leave-policy-template
https://www.dol.gov/sites/dolgov/files/WHD/legacy/files/employerguide.pdf
https://www.whosoff.com/base/content/downloads/annual-leave-policy-template.pdf
https://www.business-in-a-box.com/template/time-off-policy-D737/
https://dmec.org/wp-content/uploads/DMEC-Sample-Policy_Leave-of-Absence.pdf
https://www.astrazeneca.in/content/dam/az-in/II-2024/Leave-and-Holiday-Policy.pdf
https://www.hivedesk.com/resources/company-leave-policy-template
https://www.blog.springworks.in/leave-policy-free-template/
https://www.oswego.edu/human-resources/sites/www.oswego.edu.human-resources/files/nysorientationhandbook.pdf
https://admin.sc.gov/services/state-human-resources/benefits-and-leave/annual-leave
https://personnel.wv.gov/employee-resources/paid-leave-information-and-forms
https://www.soah.texas.gov/employee-leave-policy
https://www.sus.edu/assets/sus/systempolicies/System-Policies/07/7-012.pdf
https://familyfriendlytampabay.org/wp-content/uploads/2018/02/SampleLeavePoliciesandPointersWAPELRA-89351.pdf
https://www.hivedesk.com/resources/employee-sick-leave-policy-template
https://hrcertification.com/blog/how-to-write-effective-leave-policies-biid1000095
https://www.basusa.com/blog/employee-leave-benefits-a-guide-for-hr-professionals
https://kingcounty.gov/en/dept/dhr/about-king-county/hr-resources-employees-partners/employee-resources/policies
https://oshr.nc.gov/hr-governance/policies-all
https://www.brightmine.com/us/resources/hr-compliance/employee-leaves/leave-laws-by-state-chart/
https://paidfamilyleave.ny.gov/employer-responsibilities-and-resources
https://www.dol.gov/agencies/whd/fmla
https://benefits.adobe.com/us/time-off/leaves-of-absence

https://www.workstream.us/policy-templates/compensation-policy
https://resources.workable.com/compensation-policy-template
https://midstatehealthnetwork.org/application/files/5217/5914/1943/Human_Resources_-_Employee_Compensation_Procedure.pdf
https://www.monitask.com/forms/compensation-policy-template/
https://www.pandadoc.com/compensation-agreement-template/
https://www.business-in-a-box.com/template/salary-policy-D13392/
https://www.trec.org/wp-content/uploads/2021/04/Compensation-Philosophy-Policy-and-Samples-v825.pdf
https://cms6.revize.com/revize/highlandparkil/government/city_departments/city_manager_s_office/human_resources/docs/Compensation%20Policy%20Effective%20010119%20-%20Final.pdf
https://www.performyard.com/articles/compensation-plan-examples-and-templates
https://www.yourscvwater.com/sites/default/files/SCVWA/SCVWA-Employee-Manual-Section-35-Compensation-Policy-c1_0.pdf
https://www.opm.gov/policy-data-oversight/hiring-information/hiring-authorities/schedule-policycareer/template-for-executive-branch-agency-compensation-policies-under-schedule-policycareer.pdf
https://www.lawinsider.com/clause/salary-policy
https://www.prothman.com/JobFiles/3029/Compensation%20Policy.pdf
https://www.business-in-a-box.com/template/compensation-and-benefits-policy-D13629/
https://www.qobra.co/blog/compensation-policy-examples
https://lattice.com/templates/compensation-policy-template
https://www.nyu.edu/content/dam/nyu/compliance/documents/SPA-InstitutionalBaseSalaryPolicy.pdf
https://docs.gato.txst.edu/134763/Faculty%20Compensation%20Policy%20Summary%20FINAL.pdf
https://policy.byu.edu/content/managed/151/CompensationPolicy.pdf
https://faculty.osu.edu/sites/default/files/documents/facultycompensation_2.pdf
https://policies.tcnj.edu/wp-content/uploads/sites/247/2018/02/Compensation-2.pdf
https://www.passhe.edu/policies/documents/Policies_Procedures_Standards/Employee%20Compensation%20for%20Sponsored%20Activities%20for%20State%20System%20Universities%202018-32.pdf
https://www.sus.edu/assets/sus/SU_Board/Policies/extra-compensation.pdf
https://www.montana.edu/policy/hr_policies/pdfs/2025-0115%20Additional%20Compensation%20Adopted%20Formatted.pdf
https://www.rochester.edu/policies/policy/compensation-administration/
https://www.policy.pitt.edu/sites/default/files/Policies/Employment-Related/Policy_ER_14.pdf
https://portal.ct.gov/das/services-for-state-employees/statewide-human-resources/compensation-plans
https://www.tcwglobal.com/payrolling-terms/compensation-policy
https://www.changeengine.com/articles/best-practices-for-crafting-a-compensation-policy
https://www.eeoc.gov/laws/guidance/section-10-compensation-discrimination
https://www.zoho.com/books/free-tools/compensation-policy-template/
https://www.shrm.org/topics-tools/tools/policies
https://www.indeed.com/career-advice/pay-salary/what-is-compensation-policy
https://www.benefithub.com/blog/how-to-write-a-compensation-policy
https://www.gusto.com/resources/articles/compensation-policy-examples
https://www.nishithdesai.com/fileadmin/user_upload/pdfs/Research%20Papers/Prevention_of_Sexual_Harassment_at_Workplace.pdf
https://www.ilo.org/sites/default/files/wcmsp5/groups/public/@asia/@ro-bangkok/@ilo-suva/documents/policy/wcms_407364.pdf
https://www.nifc.gov/sites/default/files/eeo/Prevention%20of%20Sexual%20Harassment%20(POSH)%20Module%20Participant%20Guide.pdf
https://www.bharatbiotech.com/corporate-governance/posh-policy.pdf
https://hexaware.com/wp-content/uploads/2024/02/i_POSH_Policy-1.pdf
https://doe.gov.in/files/inline-documents/DoE_Prevention_sexual_harassment.pdf
https://www.acas.org.uk/sexual-harassment/steps-for-employers-to-prevent-sexual-harassment
https://elearnposh.com/update-the-posh-policy-for-the-new-normal/
https://www.tuvsud.com/en-in/resource-centre/blogs/posh-what-is-prevention-of-sexual-harassment-policy-at-workplace
https://etechgroup.com/wp-content/uploads/2026/04/E-Tech-Group-POSH-Policy.pdf
https://metrobrands.com/wp-content/uploads/2025/08/Updated-PoSH-Policy-Jul25-Webiste.pdf
https://www.netwebindia.com/investors/POSH%20Policy.pdf
https://www.utkarsh.bank/uploads/pdf/our-policy/template_ten/POSH__Policy.pdf
https://www.mphasis.com/content/dam/mphasis-com/global/en/investors/governance/india-posh-policy.pdf
https://www.axisfinance.in/docs/default-source/policies-and-standards/codes---policies/policy-on-prevention-of-sexual-harassment.pdf
https://orientpaper.in/wp-content/assets/investors/code-and-policy/POSH.pdf
https://www.hul.co.in/files/origin/84b27036a3d850b91dc1e261fcf3c2a7852c4f0f.pdf/POSH_Policy_WYSNFQ%20(2).pdf
https://shaktifoundation.in/wp-content/uploads/2023/06/SSEF-prevention-of-sexual-harassment-policy.pdf
https://group.jsw.in/sites/default/files/assets/downloads/infrastructure/Policies/PoSH_Policy_JSW_Infra_140524.pdf
https://www.nestle.in/sites/g/files/pydnoa451/files/investors/documents/nestlé-india-posh.pdf
https://lowes.co.in/wp-content/uploads/2024/08/Prevention-of-Sexual-Harrasment-policy.pdf
https://nbccindia.in/pdfData/policies/NBCC%20POSH%20POLICY_02092024.pdf
https://www.gehealthcare.in/-/jssmedia/gehc/in/files/about-us/corporate-governance-ge-bel/ge-be-posh-members.pdf
https://outpost-vfx.com/media/pages/posh-policy/855936ebe3-1697126416/outpost_poshpolicy23.pdf
https://www.bata.com/in/posh-policy.html
https://www.wipro.com/content/dam/nexus/en/investor/corporate-governance/policies-and-guidelines/ethical-guidelines/global-policy-on-prevention-of-sexual-harassment.pdf
https://vipaindia.com/wp-content/uploads/2023/07/POSH-Policy-VIPA.pdf
https://goglobal.com/legal-policies/legal-policies-posh-policy-india/
https://www.policycentral.ai/blogs/hr-policy-management/posh-policy-requirements-indian-companies/
https://www.infosys.com/investors/corporate-governance/policies/posh-policy.pdf
https://www.relianceindustries.com/pdf/RIL-POSH-Policy.pdf
https://www.bajajfinserv.in/sites/default/files/2021-04/Bajaj-Finserv-POSH-Policy.pdf
https://www.techmahindra.com/en-in/corporate-governance/policies/posh-policy/
https://www.tcs.com/content/dam/global-tcs/en/pdfs/investor/posh-policy.pdf
https://www.larsentoubro.com/media/49871/posh-policy.pdf
https://policies.syr.edu/policies/administrative-and-financial/expenses-reimbursement-of/
https://auburnpub.cfmnetwork.com/B.aspx?BookId=12260&PageId=460638
https://www.business-in-a-box.com/template/company-reimbursement-policy-D13628
https://www.asc.upenn.edu/policies-resources/annenberg-school-business-office/travel-reimbursement-policies
https://ibuy.gwu.edu/sites/g/files/zaxdzs4686/files/2024-02/travel_business_expense_reimbursement_manual_02-21-2024.pdf
https://mrsc.org/explore-topics/personnel/policies/travel-expense-reimbursement
https://berea.smartcatalogiq.com/en/current/faculty-manual/selected-institution-wide-policies/travel-and-business-expense-reimbursement-policy-excerpt
https://procurement.uark.edu/policy/Personal_Reimbursement_Policy.pdf
https://vitl.net/wp-content/uploads/2023/09/Employee-Expense-Reimbursement-Policy-2023-APPROVED-External-Use.pdf
https://smartgivers.org/wp-content/uploads/2019/04/Sample-Expense-Reimbursement-Policy.docx
https://www.bu.edu/policies/6-4-1-travel-and-business-expense-policy/
https://www.aromaswaterdistrict.org/files/91962ceca/4.+Board+Reimbursement+Policy.pdf
https://www.calbar.ca.gov/Portals/0/documents/forms/Travel-Expense-VOL.pdf
https://policy.doc.mn.gov/DocPolicy/PolicyDoc?name=104.461.pdf
https://finance.utah.gov/state-agency-resources/policy/10-6/
https://www.hamiltonma.gov/wp-content/uploads/2018/08/Travel-Reimbursement.pdf
https://edpm.dc.gov/chapter/40/
https://www.chicago.gov/content/dam/city/depts/mayor/Press%20Room/Press%20Releases/2011/September/CCCEmployeeReimbursementPolicy.pdf
https://personnel.lacity.gov/employee-resources/engagement-training/training-reimbursements.html
https://benefits.calhr.ca.gov/state-employees/work-resources/travel-reimbursements/
https://das.nebraska.gov/accounting/erd.html
https://www.uhcprovider.com/en/policies-protocols/commercial-policies/commercial-reimbursement-policies.html
https://www.hazelhawkins.com/documents/content/Travel-Business-Expense-Reimbursement-Policy.pdf
https://www.dol.gov/agencies/olms/compliance-assistance/tips/reimbursed-travel-expense-payments
https://www.business-in-a-box.com/template/travel-expense-policy-D13627/
https://resources.workable.com/travel-expense-reimbursement-policy-template
https://www.alaan.com/blog/small-business-expense-reimbursement-best-practices
https://www.zenefits.com/workest/travel-expense-reimbursement-policy-template/
https://www.gusto.com/resources/articles/travel-expense-reimbursement-policy
https://www.paychex.com/articles/finance/expense-reimbursement-policy
https://www.adp.com/resources/articles-and-insights/articles/t/travel-expense-reimbursement.aspx
https://www.shrm.org/topics-tools/tools/travel-reimbursement-policy
https://www.indeed.com/career-advice/career-development/expense-reimbursement-policy-template
https://www.paycom.com/resources/blog/how-to-create-a-travel-reimbursement-policy/
https://www.rippling.com/blog/travel-expense-policy
https://resources.workable.com/employee-code-of-conduct-company-policy
https://documentero.com/templates/legal-contracts/document/code-of-conduct-policy/
https://www.business-in-a-box.com/template/code-of-conduct-D13318/
https://communityfoundations.ca/wp-content/uploads/2021/08/HR-Guide_-Policy-and-Procedure-Template.pdf
https://www.digitaldocumentsdirect.com/blog/free-code-of-conduct-policy-download-yours-now/
https://www.aihr.com/blog/code-of-conduct-template/
https://www.page.com/sites/page-group-v3/files/2019-01/employee-code-of-conduct-201505.pdf
https://kordon.app/policy-templates/code-of-conduct-template/
https://ethics1st.cipe.org/resources/free-template-of-ethics-policy-and-code-of-business-conduct/
https://business.vic.gov.au/__data/assets/word_doc/0020/1009550/HR-policies-and-procedures-manual-template.docx
https://s205.q4cdn.com/210152132/files/doc_governance/2024/May/code-of-business-conduct-ethics-2024_external.pdf
https://www.accobrands.com/siteassets/code-of-conduct/pdf/codeofconduct_2025_english_1761251489.pdf
https://ir.thomsonreuters.com/static-files/f4169de5-ee8c-4c28-9971-75b0baf97365
https://static.conocophillips.com/files/resources/conocophillips_codeofethics.pdf
https://us.orexo.com/media/yvwjdc0p/cl-004-07-orexo-us-code-of-business-conduct-ethics-aug-2022.pdf
https://www.reynoldsconsumerproducts.com/sites/default/files/2020-10/Statement%20of%20Business%20Principles%20and%20Code%20of%20Conduct%20Policy.pdf
https://d2f5upgbvkx8pz.cloudfront.net/sites/default/files/inline-files/Code_of_Conduct_14.pdf
https://esg.cmc.com/wp-content/uploads/Code-of-Conduct-10.14.24-FINAL_English.pdf
https://multimedia.3m.com/mws/media/1237516O/3m-global-code-of-conduct.pdf
https://goldenagri.com.sg/wp-content/uploads/2016/01/Code_of_Conduct_-_English_final2.pdf
https://envirofly-group.com/wp-content/uploads/2024/06/ENVIROFLY-HR-PolicyCode-of-Conduct.pdf
https://meetings.cotswold.gov.uk/documents/s10114/Part%20E2%20Employee%20Conduct%20of%20Conduct%20Policy.pdf
https://www.portseattle.org/sites/default/files/2022-04/port-code-of-conduct-master.pdf
https://alliancebioversityciat.org/sites/default/files/documents/po-12-hr_alliance-code-of-ethics-and-conduct-25.09.2020-1.pdf
https://filecache.investorroom.com/mr5ir_comerica/466/2022%20Code%20of%20Business%20Conduct%20and%20Ethics%20for%20Employees.pdf
https://hrpa.s3.amazonaws.com/uploads/2022/08/HRPA-Code-of-Ethics-and-Rules-of-Professional-Conduct.pdf
https://content.equisolve.net/ups/db/1097/9987/file/Code+of+Conduct+and+Ethics.pdf
https://www.unitedhealthgroup.com/content/dam/UHG/PDF/About/UNH-Code-of-Conduct.pdf
https://www.rippling.com/blog/code-of-conduct-examples
https://www.indeed.com/career-advice/career-development/code-of-conduct-examples
https://www.hracuity.com/resources/templates/code-of-conduct-template/
https://www.zenefits.com/workest/code-of-conduct-policy-template/
https://www.gusto.com/resources/articles/employee-code-of-conduct-policy
https://www.paychex.com/articles/human-resources/employee-code-of-conduct
https://www.shrm.org/resourcesandtools/tools-and-samples/policies/pages/cms_000585.aspx

"""

# Run the function and display results
output_urls = format_urls(url_paragraph)

print("Formatted Output:")
for url in output_urls:
    print(url)
