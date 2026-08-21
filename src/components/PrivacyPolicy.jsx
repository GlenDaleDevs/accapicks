import { Link } from "react-router-dom";
import "./LegalPages.css";

function PrivacyPolicy() {
  return (
    <div className="legal-page">
      <div className="legal-header">
        <Link to="/" className="back-link">← Back to AccaPicks</Link>
        <h1>Privacy Policy</h1>
        <p className="legal-date">Effective Date: August 21, 2026</p>
      </div>

      <div className="legal-content">
        <section>
          <h2>1. INTRODUCTION</h2>
          <p>
            Welcome to AccaPicks ("we", "our", "us"). We operate the website accapicks.com (the "Platform"), a social sports prediction and accumulator tracking service.
          </p>
          <p>
            This Privacy Policy explains how we collect, use, store, and protect your personal information when you use our Platform. We are committed to protecting your privacy and complying with the UK General Data Protection Regulation (UK GDPR) and the Data Protection Act 2018.
          </p>
          <p>
            <strong>Data Controller:</strong><br />
            AccaPicks<br />
            Email: glen.dev@outlook.com
          </p>
          <p>If you have any questions about this Privacy Policy or how we handle your data, please contact us using the details above.</p>
        </section>

        <section>
          <h2>2. IMPORTANT INFORMATION</h2>
          <h3>2.1 Age Restriction</h3>
          <p>
            AccaPicks is only available to users aged 18 and over. We do not knowingly collect or process personal data from anyone under 18. If you are under 18, you must not use our Platform. If we become aware that we have collected personal data from someone under 18, we will delete that information promptly.
          </p>
          <h3>2.2 Our Platform Is Not a Gambling Service</h3>
          <p>
            AccaPicks does not operate as a gambling platform. You cannot place real-money bets through our service. We provide a social platform where users can track sports predictions and compare accumulator picks with friends. Any betting activity takes place on third-party bookmaker websites (accessed via affiliate links), which are separately regulated.
          </p>
        </section>

        <section>
          <h2>3. INFORMATION WE COLLECT</h2>
          <h3>3.1 Information You Provide Directly</h3>
          <p>When you create an account and use our Platform, we collect:</p>
          <p><strong>a) Account Information:</strong></p>
          <ul>
            <li>Email address</li>
            <li>Username (your chosen display name)</li>
            <li>Password (stored in hashed format only - we never store plain text passwords)</li>
          </ul>
          <p><strong>b) User-Generated Content:</strong></p>
          <ul>
            <li>Group memberships and invitations</li>
            <li>Your betting picks and predictions (accumulators you create)</li>
            <li>Match selections and stake amounts (for tracking purposes only)</li>
          </ul>

          <h3>3.2 Information We Collect Automatically</h3>
          <p>When you use our Platform, we automatically collect:</p>
          <p><strong>a) Usage Data:</strong></p>
          <ul>
            <li>Pages you visit on the Platform</li>
            <li>Features and functions you use</li>
            <li>Time spent on different pages</li>
            <li>Groups you join or create</li>
            <li>Frequency of platform access</li>
          </ul>
          <p><strong>b) Technical Data:</strong></p>
          <ul>
            <li>IP address</li>
            <li>Browser type and version</li>
            <li>Device type and operating system</li>
            <li>Time zone settings</li>
            <li>Referring website addresses</li>
            <li>Push notification subscription details (if you enable notifications), including your device's push endpoint and encryption keys</li>
          </ul>
          <p><strong>c) Cookies and Similar Technologies:</strong></p>
          <p>See Section 9 (Cookies) for detailed information</p>

          <h3>3.3 Information We Do NOT Collect</h3>
          <p>We do not collect or process:</p>
          <ul>
            <li>Payment card information (we don't process payments)</li>
            <li>Real betting transaction data (this occurs on third-party bookmaker sites)</li>
            <li>Sensitive personal data (racial/ethnic origin, political opinions, religious beliefs, health data, etc.)</li>
          </ul>
        </section>

        <section>
          <h2>4. LEGAL BASIS FOR PROCESSING YOUR DATA</h2>
          <p>Under UK GDPR, we must have a lawful basis to process your personal data. We rely on the following legal bases:</p>
          <h3>4.1 Contract (Article 6(1)(b) UK GDPR)</h3>
          <p>Processing necessary to provide our Platform services to you, including:</p>
          <ul>
            <li>Creating and managing your account</li>
            <li>Delivering the core Platform functionality (groups, accumulators, leaderboards)</li>
            <li>Communicating essential service information</li>
          </ul>
          <h3>4.2 Consent (Article 6(1)(a) UK GDPR)</h3>
          <p>Where you have given clear consent, including:</p>
          <ul>
            <li>Email verification when you sign up</li>
            <li>Optional marketing communications (if we introduce these in future)</li>
          </ul>
          <p>You can withdraw consent at any time by contacting us or using opt-out links in emails.</p>
          <h3>4.3 Legitimate Interests (Article 6(1)(f) UK GDPR)</h3>
          <p>Processing necessary for our legitimate business interests, including:</p>
          <ul>
            <li>Improving and optimizing the Platform</li>
            <li>Analyzing usage patterns to enhance user experience</li>
            <li>Preventing fraud and ensuring Platform security</li>
            <li>Operating affiliate partnerships (bookmaker links)</li>
          </ul>
          <p>We have assessed that these interests are not overridden by your rights and freedoms.</p>
          <h3>4.4 Legal Obligation (Article 6(1)(c) UK GDPR)</h3>
          <p>Complying with legal requirements, such as:</p>
          <ul>
            <li>Responding to valid legal requests from authorities</li>
            <li>Maintaining records required by law</li>
          </ul>
        </section>

        <section>
          <h2>5. HOW WE USE YOUR INFORMATION</h2>
          <p>We use your personal data for the following purposes:</p>
          <h3>5.1 Core Platform Services</h3>
          <ul>
            <li>Create and manage your user account</li>
            <li>Authenticate your login sessions</li>
            <li>Display your username and betting picks to other group members</li>
            <li>Send a push notification to other group members when you make a pick, naming you and your selection, so they see it on their device even when the app is closed (if they've enabled notifications)</li>
            <li>Send a push notification when another member "nudges" you to make your pick, or when you nudge someone else</li>
            <li>Generate group leaderboards</li>
            <li>Track accumulator results</li>
            <li>Send verification codes and essential account emails</li>
          </ul>
          <h3>5.2 Platform Improvement</h3>
          <ul>
            <li>Analyze how users interact with features</li>
            <li>Identify popular leagues and match selections</li>
            <li>Optimize Platform performance and user experience</li>
            <li>Develop new features based on usage patterns</li>
          </ul>
          <h3>5.3 Communications</h3>
          <ul>
            <li>Send email verification codes when you register</li>
            <li>Notify you of important changes to our Platform or policies</li>
            <li>Respond to your inquiries and support requests</li>
            <li>(Future) Send promotional offers if you opt in</li>
          </ul>
          <h3>5.4 Security and Fraud Prevention</h3>
          <ul>
            <li>Detect and prevent unauthorized access</li>
            <li>Monitor for suspicious activity</li>
            <li>Enforce our Terms of Service</li>
          </ul>
          <h3>5.5 Legal Compliance</h3>
          <ul>
            <li>Respond to legal requests and court orders</li>
            <li>Enforce our legal rights</li>
            <li>Comply with applicable laws and regulations</li>
          </ul>
        </section>

        <section>
          <h2>6. DATA SHARING AND THIRD-PARTY SERVICES</h2>
          <p>We do not sell your personal data to third parties. We only share your data with trusted service providers and in specific circumstances:</p>
          <h3>6.1 Third-Party Service Providers</h3>
          <p><strong>a) Resend (Email Delivery)</strong></p>
          <ul>
            <li>Purpose: Sends verification codes and transactional emails</li>
            <li>Data Shared: Email address, verification codes</li>
            <li>Location: EU/EEA servers</li>
            <li>Privacy Policy: <a href="https://resend.com/legal/privacy-policy" target="_blank" rel="noopener noreferrer">https://resend.com/legal/privacy-policy</a></li>
          </ul>
          <p><strong>b) Railway (Hosting Infrastructure)</strong></p>
          <ul>
            <li>Purpose: Hosts our Platform and database</li>
            <li>Data Shared: All data stored on the Platform</li>
            <li>Location: EU data centers</li>
            <li>Privacy Policy: <a href="https://railway.app/legal/privacy" target="_blank" rel="noopener noreferrer">https://railway.app/legal/privacy</a></li>
          </ul>
          <p><strong>c) The-Odds-API (Sports Odds Data)</strong></p>
          <ul>
            <li>Purpose: Provides match odds for display on the Platform</li>
            <li>Data Shared: None - we only receive odds data, we don't send user data</li>
            <li>Privacy Policy: <a href="https://the-odds-api.com/privacy-policy" target="_blank" rel="noopener noreferrer">https://the-odds-api.com/privacy-policy</a></li>
          </ul>
          <p><strong>d) football-data.co.uk (Match Statistics and Standings)</strong></p>
          <ul>
            <li>Purpose: Provides team form, league standings, and historic fixture data for display on the Platform</li>
            <li>Data Shared: None - we only receive match data, we don't send user data</li>
          </ul>
          <p><strong>e) Push Notification Services (Apple APNs / Google FCM / Mozilla Autopush)</strong></p>
          <ul>
            <li>Purpose: Delivers push notifications (picks and nudges) to your browser or device</li>
            <li>Data Shared: Your push subscription endpoint, and the content of the notification (e.g. a group member's username and pick) for messages addressed to you</li>
            <li>Location: Depends on your browser or device platform (Apple, Google, or Mozilla infrastructure)</li>
          </ul>

          <h3>6.2 Affiliate Partners (Bookmakers)</h3>
          <p>
            When you click on a bookmaker link on our Platform, you will be directed to an external third-party website. These bookmakers are separately regulated gambling operators with their own privacy policies. We may receive a commission if you register or place bets with them, but we do NOT share your AccaPicks account data with bookmakers.
          </p>
          <p>The bookmaker website will collect its own data about you according to their privacy policy. Please review their terms before registering.</p>

          <h3>6.3 Legal Requirements</h3>
          <p>We may disclose your information if required by law or in response to:</p>
          <ul>
            <li>Valid legal processes (court orders, subpoenas)</li>
            <li>Requests from law enforcement or regulatory authorities</li>
            <li>Protection of our legal rights or the safety of others</li>
            <li>Investigation of fraud or security issues</li>
          </ul>

          <h3>6.4 Business Transfers</h3>
          <p>
            If AccaPicks is involved in a merger, acquisition, or sale of assets, your personal data may be transferred as part of that transaction. We will notify you via email and/or a prominent notice on the Platform before your data is transferred and becomes subject to a different privacy policy.
          </p>

          <h3>6.5 With Your Consent</h3>
          <p>We may share your data for other purposes with your explicit consent.</p>

          <h3>6.6 Public Invite Links</h3>
          <p>
            If you hold a valid invite link to a group, you can see that group's name and its member count before creating an account or signing in. No other group or member data is shown to unauthenticated visitors.
          </p>
        </section>

        <section>
          <h2>7. DATA SECURITY</h2>
          <p>We take the security of your personal data seriously and implement appropriate technical and organizational measures:</p>
          <h3>7.1 Security Measures</h3>
          <ul>
            <li>Passwords are hashed using bcrypt (industry-standard cryptographic hashing)</li>
            <li>HTTPS/TLS encryption for all data transmitted to and from the Platform</li>
            <li>Secure database access controls and authentication</li>
            <li>Regular security updates and patches</li>
            <li>Limited employee access to personal data (need-to-know basis)</li>
          </ul>
          <h3>7.2 Your Responsibility</h3>
          <ul>
            <li>Choose a strong, unique password for your account</li>
            <li>Do not share your login credentials with others</li>
            <li>Log out when using shared or public computers</li>
            <li>Report any suspected security breaches to us immediately</li>
          </ul>
          <h3>7.3 No Guarantee</h3>
          <p>While we implement robust security measures, no internet transmission or electronic storage method is 100% secure. We cannot guarantee absolute security but will notify you promptly in the event of a data breach as required by law.</p>
        </section>

        <section>
          <h2>8. DATA RETENTION</h2>
          <p>We retain your personal data only for as long as necessary to fulfill the purposes outlined in this Privacy Policy, unless a longer retention period is required or permitted by law.</p>
          <h3>8.1 Retention Periods</h3>
          <p><strong>Account Data:</strong></p>
          <ul>
            <li>Retained while your account is active</li>
            <li>Deleted within 90 days of account closure or deletion request</li>
          </ul>
          <p><strong>Betting Picks and User-Generated Content:</strong></p>
          <ul>
            <li>Retained while your account is active</li>
            <li>Anonymized or deleted within 90 days of account closure</li>
          </ul>
          <p><strong>Usage and Technical Data:</strong></p>
          <ul>
            <li>Retained for up to 24 months for analytics purposes</li>
            <li>Aggregated data (without personal identifiers) may be retained indefinitely</li>
          </ul>
          <p><strong>Email Communications:</strong></p>
          <ul>
            <li>Transactional emails (verification codes): retained for 90 days</li>
            <li>Support correspondence: retained for 3 years</li>
          </ul>
          <p><strong>Legal Compliance Data:</strong></p>
          <ul>
            <li>Retained as long as required by applicable law or to defend legal claims</li>
          </ul>
          <h3>8.2 Account Deletion</h3>
          <p>When you delete your account or request data deletion:</p>
          <ul>
            <li>Your email, username, and password are permanently deleted</li>
            <li>Your betting picks are anonymized (no longer linked to you)</li>
            <li>Group memberships are removed</li>
            <li>You will no longer appear on leaderboards</li>
          </ul>
          <p>Some data may be retained in backups for up to 90 days before permanent deletion.</p>
        </section>

        <section>
          <h2>9. COOKIES AND TRACKING TECHNOLOGIES</h2>
          <h3>9.1 What Are Cookies?</h3>
          <p>Cookies are small text files stored on your device when you visit websites. They help websites remember your preferences and improve functionality.</p>
          <h3>9.2 Cookies We Use</h3>
          <p><strong>a) Essential Cookies (Strictly Necessary)</strong></p>
          <ul>
            <li>Authentication tokens (JWT stored in localStorage)</li>
            <li>Session management</li>
            <li>Security features</li>
          </ul>
          <p>Legal Basis: These are necessary for the Platform to function and do not require consent under UK GDPR.</p>
          <p><strong>b) Performance and Analytics Cookies (Future Implementation)</strong></p>
          <ul>
            <li>Usage statistics</li>
            <li>Feature interaction tracking</li>
            <li>Error reporting</li>
          </ul>
          <p>Legal Basis: Consent. We will request your consent before implementing analytics cookies.</p>
          <h3>9.3 Third-Party Cookies</h3>
          <p>
            Currently, we do not use third-party cookies. If we introduce analytics services (e.g., Google Analytics) in the future, we will update this policy and request your consent.
          </p>
          <p>Bookmaker websites you visit via our affiliate links will set their own cookies according to their privacy policies.</p>
          <h3>9.4 Managing Cookies</h3>
          <p>Most browsers allow you to:</p>
          <ul>
            <li>View and delete cookies</li>
            <li>Block third-party cookies</li>
            <li>Block all cookies (note: this may prevent the Platform from functioning)</li>
          </ul>
          <p>To manage cookies, access your browser settings:</p>
          <ul>
            <li>Chrome: Settings &gt; Privacy and Security &gt; Cookies</li>
            <li>Firefox: Settings &gt; Privacy &amp; Security &gt; Cookies</li>
            <li>Safari: Preferences &gt; Privacy &gt; Cookies</li>
            <li>Edge: Settings &gt; Cookies and Site Permissions</li>
          </ul>
          <p>Note: Blocking essential cookies will prevent you from logging in and using the Platform.</p>

          <h3>9.5 Push Notifications</h3>
          <p>
            If you enable push notifications, we store a push subscription (a device- or browser-specific endpoint and encryption keys) so we can deliver alerts about picks and nudges in your groups, as described in Section 5.1. Push notifications are permission-based - your browser or device asks you before enabling them, and you can revoke permission at any time through your browser or device notification settings. Revoking permission stops future notifications; it doesn't otherwise affect your account.
          </p>
        </section>

        <section>
          <h2>10. YOUR RIGHTS UNDER UK GDPR</h2>
          <p>Under UK GDPR, you have the following rights regarding your personal data:</p>
          <h3>10.1 Right of Access (Article 15)</h3>
          <p>You can request a copy of the personal data we hold about you. We will provide this in a structured, commonly used, and machine-readable format.</p>
          <h3>10.2 Right to Rectification (Article 16)</h3>
          <p>You can request correction of inaccurate or incomplete personal data. You can update your username and email address directly in your account settings.</p>
          <h3>10.3 Right to Erasure / "Right to be Forgotten" (Article 17)</h3>
          <p>You can request deletion of your personal data in certain circumstances:</p>
          <ul>
            <li>The data is no longer necessary for the purposes we collected it</li>
            <li>You withdraw consent (where consent was the legal basis)</li>
            <li>You object to processing and there are no overriding legitimate grounds</li>
            <li>The data was unlawfully processed</li>
          </ul>
          <p>Note: We may retain certain data if required by law or to defend legal claims.</p>
          <h3>10.4 Right to Restriction of Processing (Article 18)</h3>
          <p>You can request that we limit how we use your data in certain situations:</p>
          <ul>
            <li>You contest the accuracy of the data</li>
            <li>The processing is unlawful but you don't want it erased</li>
            <li>We no longer need the data but you need it for legal claims</li>
            <li>You have objected to processing pending verification of our legitimate grounds</li>
          </ul>
          <h3>10.5 Right to Data Portability (Article 20)</h3>
          <p>You can request a copy of your data in a portable format (e.g., JSON) and transmit it to another service provider where technically feasible.</p>
          <h3>10.6 Right to Object (Article 21)</h3>
          <p>You can object to processing based on legitimate interests or for direct marketing purposes. We will stop processing unless we have compelling legitimate grounds that override your rights.</p>
          <h3>10.7 Right to Withdraw Consent</h3>
          <p>Where processing is based on consent, you can withdraw it at any time. This does not affect the lawfulness of processing before withdrawal.</p>
          <h3>10.8 Right Not to Be Subject to Automated Decision-Making (Article 22)</h3>
          <p>We do not currently use automated decision-making or profiling that produces legal or similarly significant effects.</p>
          <h3>10.9 How to Exercise Your Rights</h3>
          <p>To exercise any of these rights, contact us at:</p>
          <p>Email: glen.dev@outlook.com<br />Subject: Data Rights Request</p>
          <p>Please include:</p>
          <ul>
            <li>Your username and registered email address</li>
            <li>Description of your request</li>
            <li>Proof of identity (to prevent unauthorized access)</li>
          </ul>
          <p>We will respond to your request within one month. In complex cases, we may extend this by two additional months and will notify you of the extension.</p>
        </section>

        <section>
          <h2>11. INTERNATIONAL DATA TRANSFERS</h2>
          <h3>11.1 Data Storage Location</h3>
          <p>Your personal data is primarily stored on servers located in the European Economic Area (EEA) through our hosting provider Railway.</p>
          <h3>11.2 Transfers Outside the UK/EEA</h3>
          <p>Some of our service providers may process data outside the UK/EEA. Where this occurs, we ensure adequate protection through:</p>
          <ul>
            <li>Standard Contractual Clauses (SCCs) approved by the UK Information Commissioner's Office (ICO)</li>
            <li>Adequacy decisions (where the destination country is deemed to have adequate data protection laws)</li>
            <li>Other appropriate safeguards under UK GDPR</li>
          </ul>
          <h3>11.3 Email Service Provider (Resend)</h3>
          <p>Resend operates within the EU/EEA. Email data is not transferred outside these regions.</p>
          <h3>11.4 Your Rights</h3>
          <p>If your data is transferred internationally, you retain all rights under UK GDPR, including the right to request details of the safeguards in place.</p>
        </section>

        <section>
          <h2>12. CHILDREN'S PRIVACY</h2>
          <p>AccaPicks is strictly for users aged 18 and over. We do not knowingly collect personal data from anyone under 18 years of age.</p>
          <p>If you are under 18, you must not:</p>
          <ul>
            <li>Create an account</li>
            <li>Use the Platform</li>
            <li>Provide any personal information to us</li>
          </ul>
          <p>If we become aware that we have collected personal data from someone under 18, we will:</p>
          <ul>
            <li>Delete that information immediately</li>
            <li>Terminate the account</li>
            <li>Notify the user (if possible)</li>
          </ul>
          <p>Parents and Guardians: If you believe your child under 18 has provided personal data to us, please contact us immediately at glen.dev@outlook.com so we can delete it.</p>
        </section>

        <section>
          <h2>13. CHANGES TO THIS PRIVACY POLICY</h2>
          <h3>13.1 Updates</h3>
          <p>We may update this Privacy Policy from time to time to reflect:</p>
          <ul>
            <li>Changes in our data practices</li>
            <li>New features or services</li>
            <li>Legal or regulatory requirements</li>
            <li>Industry best practices</li>
          </ul>
          <h3>13.2 Notification</h3>
          <p>When we make material changes to this Privacy Policy, we will:</p>
          <ul>
            <li>Update the "Last Updated" date at the top of this document</li>
            <li>Notify you via email to your registered email address</li>
            <li>Display a prominent notice on the Platform for 30 days</li>
          </ul>
          <h3>13.3 Continued Use</h3>
          <p>Your continued use of the Platform after changes take effect constitutes acceptance of the updated Privacy Policy. If you do not agree with the changes, you should stop using the Platform and may request account deletion.</p>
          <h3>13.4 Version History</h3>
          <p>We maintain records of previous versions of this Privacy Policy. You can request historical versions by contacting us.</p>
        </section>

        <section>
          <h2>14. LINKS TO EXTERNAL WEBSITES</h2>
          <p>Our Platform contains links to external third-party websites, including:</p>
          <ul>
            <li>Bookmaker websites (via affiliate links)</li>
            <li>Social media platforms</li>
            <li>Partner services</li>
          </ul>
          <p>
            We are not responsible for the privacy practices or content of these external websites. Each third-party site has its own privacy policy, which we encourage you to review before providing any personal information.
          </p>
          <p>When you click a link and leave AccaPicks, you are subject to the privacy policy of the destination website.</p>
        </section>

        <section>
          <h2>15. GLOSSARY</h2>
          <p>"Personal Data" means any information relating to an identified or identifiable individual.</p>
          <p>"Processing" means any operation performed on personal data, including collection, storage, use, disclosure, or deletion.</p>
          <p>"Data Controller" means the entity that determines the purposes and means of processing personal data (AccaPicks).</p>
          <p>"Data Processor" means an entity that processes personal data on behalf of the data controller (e.g., our hosting provider).</p>
          <p>"UK GDPR" means the General Data Protection Regulation as it forms part of UK law by virtue of section 3 of the European Union (Withdrawal) Act 2018.</p>
          <p>"Consent" means any freely given, specific, informed, and unambiguous indication of the data subject's agreement to processing of personal data.</p>
        </section>

        <section>
          <h2>16. CONTACT INFORMATION</h2>
          <h3>16.1 Data Controller</h3>
          <p>AccaPicks</p>
          <h3>16.2 Contact Details</h3>
          <p>For privacy-related inquiries, data rights requests, or complaints:</p>
          <p>Email: glen.dev@outlook.com<br />Subject: Privacy Inquiry / Data Rights Request</p>
          <p>Response Time: We aim to respond to all inquiries within 5 business days and resolve data rights requests within one month.</p>
          <h3>16.3 Supervisory Authority</h3>
          <p>You have the right to lodge a complaint with the UK's supervisory authority for data protection:</p>
          <p>
            <strong>Information Commissioner's Office (ICO)</strong><br />
            Wycliffe House<br />
            Water Lane<br />
            Wilmslow<br />
            Cheshire<br />
            SK9 5AF
          </p>
          <p>Telephone: 0303 123 1113<br />Website: <a href="https://ico.org.uk/make-a-complaint/" target="_blank" rel="noopener noreferrer">https://ico.org.uk/make-a-complaint/</a></p>
          <p>We encourage you to contact us first so we can address your concerns, but you have the right to complain to the ICO at any time.</p>
        </section>

        <section>
          <h2>17. ACKNOWLEDGMENT</h2>
          <p>By using AccaPicks, you acknowledge that you have read, understood, and agree to be bound by this Privacy Policy.</p>
          <p>If you do not agree with this Privacy Policy, you must not use the Platform.</p>
        </section>

        <div className="legal-footer">
          <p>Document Version: 1.1</p>
          <p>Effective Date: August 21, 2026</p>
          <p>© 2026 AccaPicks. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
}

export default PrivacyPolicy;
