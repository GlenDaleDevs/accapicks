import { Link } from "react-router-dom";
import "./LegalPages.css";

function TermsOfService() {
  return (
    <div className="legal-page">
      <div className="legal-header">
        <Link to="/" className="back-link">← Back to AccaPicks</Link>
        <h1>Terms of Service</h1>
        <p className="legal-date">Last Updated: February 5, 2026</p>
      </div>

      <div className="legal-content">
        <section>
          <h2>1. ACCEPTANCE OF TERMS</h2>
          <p>
            By accessing or using AccaPicks ("the Website", "our Service") at https://accapicks.com and https://www.accapicks.com, you agree to be bound by these Terms of Service ("Terms"). If you do not agree to these Terms, you must not use the Website.
          </p>
          <p>
            These Terms constitute a legally binding agreement between you ("User", "you") and AccaPicks ("we", "us", "our").
          </p>
        </section>

        <section>
          <h2>2. ELIGIBILITY AND AGE RESTRICTION</h2>
          <p><strong>2.1</strong> You must be at least 18 years of age to use this Website.</p>
          <p><strong>2.2</strong> By registering an account, you confirm that:</p>
          <ul>
            <li>You are 18 years of age or older</li>
            <li>You are legally permitted to access gambling-related content in your jurisdiction</li>
            <li>All information you provide during registration is accurate and complete</li>
          </ul>
          <p><strong>2.3</strong> We reserve the right to request proof of age at any time. Failure to provide satisfactory verification may result in account suspension or termination.</p>
          <p><strong>2.4</strong> Users found to be under 18 will have their accounts immediately terminated.</p>
        </section>

        <section>
          <h2>3. NATURE OF THE SERVICE</h2>
          <p><strong>3.1</strong> AccaPicks is an ENTERTAINMENT and COMPARISON service that allows users to:</p>
          <ul>
            <li>Create and join private groups with friends</li>
            <li>Build collaborative sports betting accumulators by selecting match outcomes</li>
            <li>Compare odds across multiple licensed bookmakers</li>
            <li>Track accumulator results and view group leaderboards</li>
          </ul>
          <p><strong>3.2</strong> AccaPicks does NOT:</p>
          <ul>
            <li>Accept bets or wagers of any kind</li>
            <li>Process payments or hold user funds</li>
            <li>Operate as a licensed gambling operator</li>
            <li>Guarantee the accuracy of odds displayed</li>
            <li>Facilitate gambling transactions</li>
          </ul>
          <p><strong>3.3</strong> Any actual betting activity takes place on third-party licensed bookmaker websites. We are not a party to any betting transactions you make with bookmakers.</p>
        </section>

        <section>
          <h2>4. ACCOUNT REGISTRATION AND SECURITY</h2>
          <p><strong>4.1</strong> To use the Service, you must create an account by providing:</p>
          <ul>
            <li>A valid email address</li>
            <li>A secure password</li>
            <li>Verification of your email address via a one-time code</li>
          </ul>
          <p><strong>4.2</strong> You are responsible for:</p>
          <ul>
            <li>Maintaining the confidentiality of your account credentials</li>
            <li>All activities that occur under your account</li>
            <li>Notifying us immediately of any unauthorized access</li>
          </ul>
          <p><strong>4.3</strong> You must not:</p>
          <ul>
            <li>Share your account with others</li>
            <li>Create multiple accounts</li>
            <li>Use another person's account without permission</li>
            <li>Provide false or misleading information during registration</li>
          </ul>
          <p><strong>4.4</strong> We reserve the right to suspend or terminate accounts that violate these Terms.</p>
        </section>

        <section>
          <h2>5. USER CONDUCT AND ACCEPTABLE USE</h2>
          <p><strong>5.1</strong> You agree to use the Website in compliance with all applicable laws and regulations.</p>
          <p><strong>5.2</strong> You must NOT:</p>
          <ul>
            <li>Use the Service for any unlawful purpose</li>
            <li>Harass, abuse, or harm other users</li>
            <li>Post offensive, discriminatory, or inappropriate content</li>
            <li>Attempt to gain unauthorized access to the Website or other users' accounts</li>
            <li>Use automated systems (bots, scrapers) to access the Service</li>
            <li>Reverse engineer, decompile, or attempt to extract source code</li>
            <li>Transmit viruses, malware, or other harmful code</li>
            <li>Manipulate or interfere with the proper functioning of the Service</li>
            <li>Use the Service for commercial purposes without our written consent</li>
            <li>Encourage or facilitate underage gambling</li>
          </ul>
          <p><strong>5.3</strong> We reserve the right to remove content and terminate accounts that violate these provisions.</p>
        </section>

        <section>
          <h2>6. AFFILIATE RELATIONSHIPS AND DISCLOSURE</h2>
          <p><strong>6.1</strong> AccaPicks may display affiliate links to licensed bookmaker websites.</p>
          <p><strong>6.2</strong> When you click through to a bookmaker via our affiliate links and create an account or place bets, we may receive a commission from the bookmaker.</p>
          <p><strong>6.3</strong> These affiliate relationships do NOT:</p>
          <ul>
            <li>Influence the accuracy of odds displayed</li>
            <li>Create any obligation for you to use specific bookmakers</li>
            <li>Affect the price you pay or odds you receive</li>
            <li>Make us responsible for the bookmaker's services or conduct</li>
          </ul>
          <p><strong>6.4</strong> You are free to visit bookmaker websites directly without using our affiliate links.</p>
        </section>

        <section>
          <h2>7. THIRD-PARTY BOOKMAKERS AND BETTING</h2>
          <p><strong>7.1</strong> All betting transactions occur on third-party bookmaker websites that operate independently from AccaPicks.</p>
          <p><strong>7.2</strong> Each bookmaker has its own terms and conditions, privacy policy, and licensing requirements. You are responsible for reviewing and complying with these terms before placing bets.</p>
          <p><strong>7.3</strong> We do NOT:</p>
          <ul>
            <li>Endorse or guarantee any bookmaker</li>
            <li>Accept responsibility for bookmaker conduct, errors, or disputes</li>
            <li>Control bookmaker odds, terms, or payment processing</li>
            <li>Guarantee that bookmakers will accept your bets</li>
          </ul>
          <p><strong>7.4</strong> Any disputes regarding bets, payments, or account issues with bookmakers must be resolved directly with the bookmaker concerned.</p>
        </section>

        <section>
          <h2>8. ODDS DATA AND ACCURACY</h2>
          <p><strong>8.1</strong> Odds displayed on AccaPicks are sourced from The-Odds-API and other third-party data providers.</p>
          <p><strong>8.2</strong> While we make reasonable efforts to display accurate information, we do NOT guarantee:</p>
          <ul>
            <li>The accuracy, completeness, or timeliness of odds data</li>
            <li>That odds displayed match current bookmaker odds</li>
            <li>That all bookmakers or markets are included</li>
          </ul>
          <p><strong>8.3</strong> Odds may change between viewing on AccaPicks and placing bets with bookmakers.</p>
          <p><strong>8.4</strong> Always verify odds directly with the bookmaker before placing bets.</p>
          <p><strong>8.5</strong> We are not liable for any losses resulting from inaccurate or outdated odds data.</p>
        </section>

        <section>
          <h2>9. RESPONSIBLE GAMBLING</h2>
          <p><strong>9.1</strong> AccaPicks supports responsible gambling practices.</p>
          <p><strong>9.2</strong> We remind all users that gambling should be undertaken for entertainment purposes only and can result in financial loss.</p>
          <p><strong>9.3</strong> If you believe you may have a gambling problem, please seek help:</p>
          <ul>
            <li>BeGambleAware: <a href="https://www.begambleaware.org" target="_blank" rel="noopener noreferrer">www.begambleaware.org</a> (0808 8020 133)</li>
            <li>GamCare: <a href="https://www.gamcare.org.uk" target="_blank" rel="noopener noreferrer">www.gamcare.org.uk</a> (0808 8020 133)</li>
            <li>National Gambling Helpline: 0808 8020 133</li>
          </ul>
          <p><strong>9.4</strong> Most licensed bookmakers offer self-exclusion tools, deposit limits, and reality checks. We encourage you to use these features.</p>
          <p><strong>9.5</strong> We may provide information about responsible gambling but are not responsible for your betting decisions or outcomes.</p>
        </section>

        <section>
          <h2>10. INTELLECTUAL PROPERTY RIGHTS</h2>
          <p><strong>10.1</strong> All content on AccaPicks, including but not limited to:</p>
          <ul>
            <li>Website design, layout, and graphics</li>
            <li>Software code and functionality</li>
            <li>Logos, trademarks, and branding</li>
            <li>Text, images, and other materials</li>
          </ul>
          <p>is owned by or licensed to AccaPicks and is protected by UK and international copyright, trademark, and other intellectual property laws.</p>
          <p><strong>10.2</strong> You are granted a limited, non-exclusive, non-transferable license to access and use the Website for personal, non-commercial purposes only.</p>
          <p><strong>10.3</strong> You must NOT:</p>
          <ul>
            <li>Copy, reproduce, or redistribute Website content without permission</li>
            <li>Use our trademarks or branding without written consent</li>
            <li>Create derivative works based on the Website</li>
            <li>Remove or alter copyright notices or attributions</li>
          </ul>
        </section>

        <section>
          <h2>11. USER-GENERATED CONTENT</h2>
          <p><strong>11.1</strong> You retain ownership of content you create on AccaPicks (such as group names, accumulator selections, and comments).</p>
          <p><strong>11.2</strong> By posting content on the Website, you grant us a worldwide, non-exclusive, royalty-free license to use, display, reproduce, and distribute your content in connection with operating the Service.</p>
          <p><strong>11.3</strong> You represent and warrant that:</p>
          <ul>
            <li>You own or have rights to any content you post</li>
            <li>Your content does not infringe third-party intellectual property rights</li>
            <li>Your content complies with these Terms and applicable laws</li>
          </ul>
          <p><strong>11.4</strong> We reserve the right to remove any user content that violates these Terms or is otherwise objectionable, without notice.</p>
        </section>

        <section>
          <h2>12. PRIVACY AND DATA PROTECTION</h2>
          <p><strong>12.1</strong> Your use of the Website is also governed by our <Link to="/privacy">Privacy Policy</Link>.</p>
          <p><strong>12.2</strong> By using the Service, you consent to the collection, use, and processing of your personal data as described in the Privacy Policy.</p>
          <p><strong>12.3</strong> We comply with the UK Data Protection Act 2018 and the UK General Data Protection Regulation (UK GDPR).</p>
          <p><strong>12.4</strong> You have rights regarding your personal data, including the right to access, correct, delete, or restrict processing. See our Privacy Policy for details.</p>
        </section>

        <section>
          <h2>13. LIMITATION OF LIABILITY</h2>
          <p><strong>13.1</strong> TO THE MAXIMUM EXTENT PERMITTED BY LAW, ACCAPICKS SHALL NOT BE LIABLE FOR:</p>
          <ul>
            <li>Any betting losses or financial losses incurred through third-party bookmakers</li>
            <li>Inaccurate, incomplete, or outdated odds or match data</li>
            <li>Bookmaker errors, disputes, or failure to pay winnings</li>
            <li>Unauthorized access to your account due to your failure to secure credentials</li>
            <li>Service interruptions, downtime, or technical errors</li>
            <li>Loss of data or content</li>
            <li>Any indirect, consequential, incidental, special, or punitive damages</li>
          </ul>
          <p><strong>13.2</strong> Our total liability to you for any claims arising from your use of the Service shall not exceed £100 (one hundred pounds sterling).</p>
          <p><strong>13.3</strong> Nothing in these Terms excludes or limits our liability for:</p>
          <ul>
            <li>Death or personal injury caused by negligence</li>
            <li>Fraud or fraudulent misrepresentation</li>
            <li>Any other liability that cannot be excluded under UK law</li>
          </ul>
        </section>

        <section>
          <h2>14. WARRANTIES AND DISCLAIMERS</h2>
          <p><strong>14.1</strong> THE WEBSITE IS PROVIDED ON AN "AS IS" AND "AS AVAILABLE" BASIS.</p>
          <p><strong>14.2</strong> WE MAKE NO WARRANTIES OR REPRESENTATIONS, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO:</p>
          <ul>
            <li>The accuracy, reliability, or completeness of content</li>
            <li>That the Service will be uninterrupted or error-free</li>
            <li>That defects will be corrected</li>
            <li>That the Website is free from viruses or harmful components</li>
          </ul>
          <p><strong>14.3</strong> You use the Website at your own risk.</p>
          <p><strong>14.4</strong> We do not warrant that the Service will meet your requirements or expectations.</p>
        </section>

        <section>
          <h2>15. INDEMNIFICATION</h2>
          <p><strong>15.1</strong> You agree to indemnify, defend, and hold harmless AccaPicks, its officers, directors, employees, and agents from any claims, liabilities, damages, losses, costs, or expenses (including reasonable legal fees) arising from:</p>
          <ul>
            <li>Your use of the Website</li>
            <li>Your violation of these Terms</li>
            <li>Your violation of any rights of another person or entity</li>
            <li>Your betting activities with third-party bookmakers</li>
            <li>Any content you post on the Website</li>
          </ul>
        </section>

        <section>
          <h2>16. TERMINATION</h2>
          <p><strong>16.1</strong> We reserve the right to suspend or terminate your account at any time, with or without notice, for:</p>
          <ul>
            <li>Violation of these Terms</li>
            <li>Fraudulent or illegal activity</li>
            <li>Providing false information</li>
            <li>Being under 18 years of age</li>
            <li>Any reason we deem necessary to protect the Service or other users</li>
          </ul>
          <p><strong>16.2</strong> You may terminate your account at any time by contacting us.</p>
          <p><strong>16.3</strong> Upon termination:</p>
          <ul>
            <li>Your right to use the Service immediately ceases</li>
            <li>We may delete your account data subject to our Privacy Policy</li>
            <li>Provisions of these Terms that by their nature should survive (including limitation of liability, indemnification, and governing law) will remain in effect</li>
          </ul>
        </section>

        <section>
          <h2>17. MODIFICATIONS TO TERMS</h2>
          <p><strong>17.1</strong> We reserve the right to modify these Terms at any time.</p>
          <p><strong>17.2</strong> When we make changes, we will:</p>
          <ul>
            <li>Update the "Last Updated" date at the top of this document</li>
            <li>Notify you via email or prominent notice on the Website (for material changes)</li>
          </ul>
          <p><strong>17.3</strong> Your continued use of the Website after changes take effect constitutes acceptance of the revised Terms.</p>
          <p><strong>17.4</strong> If you do not agree to modified Terms, you must stop using the Service and may terminate your account.</p>
        </section>

        <section>
          <h2>18. GOVERNING LAW AND JURISDICTION</h2>
          <p><strong>18.1</strong> These Terms are governed by and construed in accordance with the laws of England and Wales.</p>
          <p><strong>18.2</strong> Any disputes arising from these Terms or your use of the Website shall be subject to the exclusive jurisdiction of the courts of England and Wales.</p>
          <p><strong>18.3</strong> If you are a consumer resident in Scotland or Northern Ireland, you may bring proceedings in your local courts.</p>
        </section>

        <section>
          <h2>19. DISPUTE RESOLUTION</h2>
          <p><strong>19.1</strong> If you have a complaint or dispute, please contact us first. We will make reasonable efforts to resolve the issue.</p>
          <p><strong>19.2</strong> If we cannot resolve the dispute informally, you may have the right to use alternative dispute resolution services or to pursue legal action in accordance with Section 18.</p>
        </section>

        <section>
          <h2>20. SEVERABILITY</h2>
          <p><strong>20.1</strong> If any provision of these Terms is found to be invalid, illegal, or unenforceable by a court of competent jurisdiction, the remaining provisions shall continue in full force and effect.</p>
          <p><strong>20.2</strong> The invalid provision shall be modified to the minimum extent necessary to make it valid and enforceable while preserving the parties' original intent.</p>
        </section>

        <section>
          <h2>21. CONTACT INFORMATION</h2>
          <p><strong>21.1</strong> If you have any questions about these Terms or the Service, please contact us at:</p>
          <p>Email: glen.dev@outlook.com<br />Website: https://accapicks.com</p>
        </section>

        <section>
          <h2>22. ACKNOWLEDGMENT</h2>
          <p>By creating an account and using AccaPicks, you acknowledge that:</p>
          <ul>
            <li>You have read and understood these Terms of Service</li>
            <li>You agree to be bound by these Terms</li>
            <li>You are at least 18 years of age</li>
            <li>You understand that AccaPicks does not accept bets or process gambling transactions</li>
            <li>All betting occurs on third-party bookmaker websites at your own risk</li>
            <li>You are responsible for complying with gambling laws in your jurisdiction</li>
            <li>Gambling can be addictive and may result in financial loss</li>
          </ul>
        </section>

        <div className="legal-footer">
          <p>Document Version: 1.0</p>
          <p>© 2026 AccaPicks. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
}

export default TermsOfService;
