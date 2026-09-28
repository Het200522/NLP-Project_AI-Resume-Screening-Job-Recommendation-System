"""
Predefined role templates with realistic job descriptions.
Users can select a role instead of pasting a full JD.
"""
import random

ROLES: dict[str, dict] = {
    "software_engineer": {
        "id": "software_engineer",
        "title": "Software Engineer",
        "category": "Engineering",
        "description": (
            "Job Title: Software Engineer\n\n"
            "We are looking for a skilled Software Engineer to join our team. "
            "You will design, develop, and maintain scalable software solutions.\n\n"
            "Responsibilities:\n"
            "- Design, develop, and test high-quality code\n"
            "- Collaborate with cross-functional teams to define and ship new features\n"
            "- Write clean, maintainable, and well-documented code\n"
            "- Participate in code reviews and mentor junior developers\n"
            "- Troubleshoot and debug applications\n"
            "- Optimize applications for performance and scalability\n\n"
            "Required Skills:\n"
            "- Strong proficiency in Python, Java, or JavaScript\n"
            "- Experience with REST APIs and microservices architecture\n"
            "- Proficiency with Git version control\n"
            "- Solid understanding of data structures and algorithms\n"
            "- Experience with SQL and NoSQL databases\n"
            "- Knowledge of cloud services (AWS, GCP, or Azure)\n\n"
            "Preferred Skills:\n"
            "- Experience with Docker and Kubernetes\n"
            "- Familiarity with CI/CD pipelines\n"
            "- Knowledge of React, Angular, or Vue.js\n"
            "- Experience with agile methodologies\n\n"
            "Education: Bachelor's degree in Computer Science or related field\n"
            "Experience: 2-5 years of software development experience"
        ),
    },
    "data_scientist": {
        "id": "data_scientist",
        "title": "Data Scientist",
        "category": "Data & Analytics",
        "description": (
            "Job Title: Data Scientist\n\n"
            "We are seeking a talented Data Scientist to extract insights from complex datasets "
            "and build predictive models that drive business decisions.\n\n"
            "Responsibilities:\n"
            "- Analyze large datasets to identify trends and patterns\n"
            "- Build and deploy machine learning models for prediction and classification\n"
            "- Create data visualizations and dashboards for stakeholders\n"
            "- Design and run A/B tests to measure business impact\n"
            "- Collaborate with engineering teams to productionize models\n"
            "- Present findings and recommendations to leadership\n\n"
            "Required Skills:\n"
            "- Proficiency in Python (pandas, NumPy, scikit-learn)\n"
            "- Experience with machine learning algorithms (regression, classification, clustering)\n"
            "- Strong SQL skills for data extraction and manipulation\n"
            "- Experience with data visualization tools (Matplotlib, Seaborn, Tableau)\n"
            "- Knowledge of statistical analysis and hypothesis testing\n"
            "- Familiarity with Jupyter notebooks\n\n"
            "Preferred Skills:\n"
            "- Experience with deep learning frameworks (TensorFlow, PyTorch)\n"
            "- Knowledge of NLP techniques\n"
            "- Experience with big data tools (Spark, Hadoop)\n"
            "- Familiarity with cloud ML platforms (SageMaker, Vertex AI)\n\n"
            "Education: Master's or PhD in Computer Science, Statistics, or related field\n"
            "Experience: 2-4 years of data science experience"
        ),
    },
    "frontend_engineer": {
        "id": "frontend_engineer",
        "title": "Frontend Engineer",
        "category": "Engineering",
        "description": (
            "Job Title: Frontend Engineer\n\n"
            "We are looking for a Frontend Engineer to build beautiful, responsive user interfaces "
            "that delight our users.\n\n"
            "Responsibilities:\n"
            "- Develop responsive and interactive web applications\n"
            "- Translate UI/UX designs into high-quality code\n"
            "- Optimize applications for maximum speed and scalability\n"
            "- Implement state management solutions\n"
            "- Write unit and integration tests\n"
            "- Collaborate with designers and backend engineers\n\n"
            "Required Skills:\n"
            "- Expert-level JavaScript/TypeScript\n"
            "- Proficiency with React or Next.js\n"
            "- Strong CSS skills (Flexbox, Grid, Tailwind CSS)\n"
            "- Experience with RESTful APIs and GraphQL\n"
            "- Knowledge of web accessibility standards (WCAG)\n"
            "- Understanding of responsive design principles\n\n"
            "Preferred Skills:\n"
            "- Experience with server-side rendering (SSR)\n"
            "- Knowledge of state management (Redux, Zustand)\n"
            "- Familiarity with testing frameworks (Jest, Cypress)\n"
            "- Experience with design tools (Figma, Sketch)\n\n"
            "Education: Bachelor's degree in CS or equivalent experience\n"
            "Experience: 2-4 years of frontend development"
        ),
    },
    "backend_engineer": {
        "id": "backend_engineer",
        "title": "Backend Engineer",
        "category": "Engineering",
        "description": (
            "Job Title: Backend Engineer\n\n"
            "We are hiring a Backend Engineer to design and build robust server-side applications "
            "and APIs.\n\n"
            "Responsibilities:\n"
            "- Design and implement scalable backend services and APIs\n"
            "- Build and maintain database schemas and data pipelines\n"
            "- Ensure high availability and reliability of services\n"
            "- Implement security best practices and data protection\n"
            "- Monitor and optimize application performance\n"
            "- Write technical documentation\n\n"
            "Required Skills:\n"
            "- Proficiency in Python, Go, or Java\n"
            "- Experience with relational databases (PostgreSQL, MySQL)\n"
            "- Strong understanding of RESTful API design\n"
            "- Experience with message queues (RabbitMQ, Kafka)\n"
            "- Knowledge of caching strategies (Redis)\n"
            "- Understanding of authentication and authorization patterns\n\n"
            "Preferred Skills:\n"
            "- Experience with microservices architecture\n"
            "- Knowledge of containerization (Docker, Kubernetes)\n"
            "- Familiarity with cloud platforms (AWS, GCP)\n"
            "- Experience with NoSQL databases (MongoDB, DynamoDB)\n\n"
            "Education: Bachelor's degree in Computer Science or related field\n"
            "Experience: 3-6 years of backend development"
        ),
    },
    "ml_engineer": {
        "id": "ml_engineer",
        "title": "Machine Learning Engineer",
        "category": "AI & ML",
        "description": (
            "Job Title: Machine Learning Engineer\n\n"
            "We are looking for a Machine Learning Engineer to build and deploy AI systems "
            "at scale.\n\n"
            "Responsibilities:\n"
            "- Design and implement ML pipelines and model training workflows\n"
            "- Deploy and monitor ML models in production environments\n"
            "- Optimize model performance and inference latency\n"
            "- Build data preprocessing and feature engineering pipelines\n"
            "- Collaborate with data scientists to productionize research models\n"
            "- Implement MLOps best practices\n\n"
            "Required Skills:\n"
            "- Strong proficiency in Python\n"
            "- Experience with ML frameworks (TensorFlow, PyTorch, scikit-learn)\n"
            "- Knowledge of ML model deployment (ONNX, TensorRT)\n"
            "- Experience with containerization (Docker, Kubernetes)\n"
            "- Understanding of MLOps tools (MLflow, Kubeflow)\n"
            "- Proficiency with cloud ML services (SageMaker, Vertex AI)\n\n"
            "Preferred Skills:\n"
            "- Experience with LLMs and transformer architectures\n"
            "- Knowledge of vector databases (Pinecone, Weaviate)\n"
            "- Familiarity with feature stores\n"
            "- Experience with distributed training\n\n"
            "Education: Master's in CS, ML, or related field\n"
            "Experience: 3-5 years of ML engineering"
        ),
    },
    "devops_engineer": {
        "id": "devops_engineer",
        "title": "DevOps Engineer",
        "category": "Infrastructure",
        "description": (
            "Job Title: DevOps Engineer\n\n"
            "We are seeking a DevOps Engineer to build and maintain our cloud infrastructure "
            "and deployment pipelines.\n\n"
            "Responsibilities:\n"
            "- Design, implement, and manage CI/CD pipelines\n"
            "- Manage cloud infrastructure (AWS, GCP, or Azure)\n"
            "- Automate deployment, monitoring, and scaling processes\n"
            "- Ensure system security, reliability, and performance\n"
            "- Manage containerized applications with Docker and Kubernetes\n"
            "- Implement infrastructure as code (Terraform, CloudFormation)\n\n"
            "Required Skills:\n"
            "- Strong experience with AWS, GCP, or Azure\n"
            "- Proficiency with Docker and Kubernetes\n"
            "- Experience with CI/CD tools (Jenkins, GitHub Actions, GitLab CI)\n"
            "- Knowledge of infrastructure as code (Terraform, Ansible)\n"
            "- Scripting skills (Bash, Python)\n"
            "- Experience with monitoring tools (Prometheus, Grafana, Datadog)\n\n"
            "Preferred Skills:\n"
            "- Experience with service mesh (Istio, Linkerd)\n"
            "- Knowledge of GitOps workflows\n"
            "- Familiarity with serverless architectures\n"
            "- Security certifications (AWS Security Specialty)\n\n"
            "Education: Bachelor's in CS or related field\n"
            "Experience: 3-5 years of DevOps experience"
        ),
    },
    "product_manager": {
        "id": "product_manager",
        "title": "Product Manager",
        "category": "Product",
        "description": (
            "Job Title: Product Manager\n\n"
            "We are looking for a Product Manager to lead product strategy and drive "
            "the development of our core platform.\n\n"
            "Responsibilities:\n"
            "- Define product vision, strategy, and roadmap\n"
            "- Gather and prioritize user requirements through research\n"
            "- Write detailed product specifications and user stories\n"
            "- Work closely with engineering, design, and marketing teams\n"
            "- Analyze market trends and competitive landscape\n"
            "- Track and report on product KPIs and metrics\n\n"
            "Required Skills:\n"
            "- Experience with product management tools (Jira, Confluence, Aha!)\n"
            "- Strong analytical and data-driven decision making\n"
            "- Excellent communication and stakeholder management\n"
            "- Experience with agile/scrum methodologies\n"
            "- Understanding of software development lifecycle\n"
            "- Ability to translate business needs into technical requirements\n\n"
            "Preferred Skills:\n"
            "- Technical background or CS degree\n"
            "- Experience with A/B testing and experimentation\n"
            "- Knowledge of SQL and data analysis\n"
            "- Experience with B2B SaaS products\n\n"
            "Education: Bachelor's degree, MBA preferred\n"
            "Experience: 3-5 years of product management"
        ),
    },
    "ux_designer": {
        "id": "ux_designer",
        "title": "UX Designer",
        "category": "Design",
        "description": (
            "Job Title: UX Designer\n\n"
            "We are seeking a talented UX Designer to create intuitive and engaging "
            "user experiences for our products.\n\n"
            "Responsibilities:\n"
            "- Conduct user research and usability testing\n"
            "- Create wireframes, prototypes, and high-fidelity mockups\n"
            "- Design intuitive user flows and information architecture\n"
            "- Collaborate with product managers and engineers\n"
            "- Develop and maintain design systems\n"
            "- Present design solutions to stakeholders\n\n"
            "Required Skills:\n"
            "- Proficiency with Figma, Sketch, or Adobe XD\n"
            "- Strong understanding of UX principles and best practices\n"
            "- Experience with user research methodologies\n"
            "- Knowledge of HTML, CSS, and responsive design\n"
            "- Ability to create interactive prototypes\n"
            "- Strong visual design skills\n\n"
            "Preferred Skills:\n"
            "- Experience with motion design and animation\n"
            "- Knowledge of accessibility standards (WCAG)\n"
            "- Familiarity with front-end development (React, HTML/CSS)\n"
            "- Experience with design tokens and design systems\n\n"
            "Education: Bachelor's in Design, HCI, or related field\n"
            "Experience: 3-5 years of UX design experience"
        ),
    },
    "data_analyst": {
        "id": "data_analyst",
        "title": "Data Analyst",
        "category": "Data & Analytics",
        "description": (
            "Job Title: Data Analyst\n\n"
            "We are looking for a Data Analyst to turn raw data into actionable insights "
            "that inform business decisions.\n\n"
            "Responsibilities:\n"
            "- Collect, clean, and analyze large datasets\n"
            "- Build and maintain dashboards and reports\n"
            "- Identify trends, patterns, and anomalies in data\n"
            "- Support business teams with data-driven insights\n"
            "- Automate recurring reporting tasks\n"
            "- Collaborate with data engineering on data quality\n\n"
            "Required Skills:\n"
            "- Strong SQL skills for data querying\n"
            "- Proficiency in Python or R for data analysis\n"
            "- Experience with visualization tools (Tableau, Power BI, Looker)\n"
            "- Knowledge of Excel and Google Sheets (advanced functions)\n"
            "- Statistical analysis and hypothesis testing\n"
            "- Strong communication and storytelling with data\n\n"
            "Preferred Skills:\n"
            "- Experience with dbt for data transformation\n"
            "- Knowledge of cloud data warehouses (BigQuery, Snowflake)\n"
            "- Familiarity with ETL processes\n"
            "- Experience with A/B test analysis\n\n"
            "Education: Bachelor's in Statistics, Economics, CS, or related field\n"
            "Experience: 2-4 years of data analysis"
        ),
    },
    "cybersecurity_analyst": {
        "id": "cybersecurity_analyst",
        "title": "Cybersecurity Analyst",
        "category": "Security",
        "description": (
            "Job Title: Cybersecurity Analyst\n\n"
            "We are seeking a Cybersecurity Analyst to protect our systems and data "
            "from security threats.\n\n"
            "Responsibilities:\n"
            "- Monitor security alerts and investigate incidents\n"
            "- Conduct vulnerability assessments and penetration testing\n"
            "- Implement security controls and best practices\n"
            "- Respond to and manage security incidents\n"
            "- Perform security audits and compliance reviews\n"
            "- Develop security documentation and training\n\n"
            "Required Skills:\n"
            "- Experience with SIEM tools (Splunk, QRadar, Sentinel)\n"
            "- Knowledge of network security and firewalls\n"
            "- Understanding of OWASP Top 10 vulnerabilities\n"
            "- Experience with intrusion detection/prevention systems\n"
            "- Knowledge of compliance frameworks (SOC 2, ISO 27001, GDPR)\n"
            "- Scripting skills (Python, Bash, PowerShell)\n\n"
            "Preferred Skills:\n"
            "- Security certifications (CEH, CompTIA Security+, CISSP)\n"
            "- Experience with cloud security (AWS Security, Azure Security)\n"
            "- Knowledge of threat modeling\n"
            "- Experience with SOAR platforms\n\n"
            "Education: Bachelor's in Cybersecurity, CS, or related field\n"
            "Experience: 2-5 years of cybersecurity experience"
        ),
    },
    "qa_engineer": {
        "id": "qa_engineer",
        "title": "QA Engineer",
        "category": "Quality Assurance",
        "description": (
            "Job Title: QA Engineer\n\n"
            "We are looking for a QA Engineer to ensure the quality of our software products "
            "through comprehensive testing.\n\n"
            "Responsibilities:\n"
            "- Design and execute test plans and test cases\n"
            "- Perform manual and automated testing\n"
            "- Identify, document, and track bugs to resolution\n"
            "- Write and maintain automated test scripts\n"
            "- Participate in code reviews and sprint planning\n"
            "- Improve testing processes and tooling\n\n"
            "Required Skills:\n"
            "- Experience with test automation frameworks (Selenium, Cypress, Playwright)\n"
            "- Proficiency in Python or JavaScript for test scripting\n"
            "- Knowledge of API testing (Postman, REST Assured)\n"
            "- Understanding of CI/CD integration for testing\n"
            "- Experience with bug tracking tools (Jira, Bugzilla)\n"
            "- Strong analytical and problem-solving skills\n\n"
            "Preferred Skills:\n"
            "- Experience with performance testing (JMeter, Locust)\n"
            "- Knowledge of security testing (OWASP, penetration testing)\n"
            "- Familiarity with containerized testing environments\n"
            "- ISTQB certification\n\n"
            "Education: Bachelor's in CS or related field\n"
            "Experience: 2-4 years of QA experience"
        ),
    },
    "mobile_developer": {
        "id": "mobile_developer",
        "title": "Mobile Developer",
        "category": "Engineering",
        "description": (
            "Job Title: Mobile Developer\n\n"
            "We are hiring a Mobile Developer to build and maintain our iOS and Android applications.\n\n"
            "Responsibilities:\n"
            "- Design and build mobile applications for iOS and/or Android\n"
            "- Collaborate with design and backend teams\n"
            "- Ensure performance, quality, and responsiveness of applications\n"
            "- Identify and fix bugs, and improve application performance\n"
            "- Publish apps to App Store and Google Play\n"
            "- Implement push notifications and offline capabilities\n\n"
            "Required Skills:\n"
            "- Proficiency in React Native, Flutter, or native (Swift/Kotlin)\n"
            "- Experience with mobile UI/UX best practices\n"
            "- Knowledge of RESTful APIs and mobile networking\n"
            "- Understanding of mobile app lifecycle management\n"
            "- Experience with local storage and databases (SQLite, Realm)\n"
            "- Familiarity with app store submission processes\n\n"
            "Preferred Skills:\n"
            "- Experience with CI/CD for mobile (Fastlane, Bitrise)\n"
            "- Knowledge of mobile testing frameworks\n"
            "- Familiarity with Firebase services\n"
            "- Experience with offline-first architecture\n\n"
            "Education: Bachelor's in CS or related field\n"
            "Experience: 2-5 years of mobile development"
        ),
    },
    "cloud_architect": {
        "id": "cloud_architect",
        "title": "Cloud Architect",
        "category": "Infrastructure",
        "description": (
            "Job Title: Cloud Architect\n\n"
            "We are looking for a Cloud Architect to design and oversee our cloud computing strategy.\n\n"
            "Responsibilities:\n"
            "- Design cloud architecture solutions for business needs\n"
            "- Lead cloud migration and modernization initiatives\n"
            "- Ensure cloud security, compliance, and cost optimization\n"
            "- Establish cloud governance and best practices\n"
            "- Evaluate and select cloud services and vendors\n"
            "- Mentor engineering teams on cloud best practices\n\n"
            "Required Skills:\n"
            "- Expert knowledge of AWS, Azure, or GCP\n"
            "- Experience with infrastructure as code (Terraform, CloudFormation)\n"
            "- Knowledge of containerization (Docker, Kubernetes)\n"
            "- Understanding of networking, security, and compliance\n"
            "- Experience with serverless architectures\n"
            "- Cost optimization and FinOps practices\n\n"
            "Preferred Skills:\n"
            "- Cloud certifications (AWS Solutions Architect, Azure Architect)\n"
            "- Experience with multi-cloud and hybrid cloud strategies\n"
            "- Knowledge of data lake and analytics architectures\n"
            "- Experience with disaster recovery and business continuity\n\n"
            "Education: Bachelor's in CS or related field\n"
            "Experience: 5-8 years of cloud architecture"
        ),
    },
}


def list_roles() -> list[dict]:
    """Return all available roles with id, title, and category."""
    return [
        {"id": r["id"], "title": r["title"], "category": r["category"]}
        for r in ROLES.values()
    ]


def get_role(role_id: str) -> dict | None:
    """Return a role's full template including the job description."""
    return ROLES.get(role_id)
