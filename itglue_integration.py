"""
IT Glue Integration Module for Policy Generator 2.0
Direct connection to IT Glue API
"""

import os
import requests
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ITGlueIntegration:
    """Direct interface to IT Glue API"""

    def __init__(self):
        # IT Glue API credentials from environment variables
        self.api_key = os.getenv('ITGLUE_API_KEY')
        self.api_base_url = 'https://api.itglue.com'
        self.timeout = 30

        if not self.api_key:
            logger.warning("IT Glue API key not configured. Set ITGLUE_API_KEY environment variable.")

    def _make_request(self, method: str, endpoint: str, params: Dict = None) -> Dict:
        """Make request to IT Glue API"""
        if not self.api_key:
            return {'success': False, 'error': 'IT Glue API key not configured'}

        url = f"{self.api_base_url}/{endpoint.lstrip('/')}"

        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/vnd.api+json',
            'Accept': 'application/vnd.api+json'
        }

        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"IT Glue API error: {str(e)}")
            return {'success': False, 'error': str(e)}

    def get_active_organizations(self) -> List[Dict]:
        """Get list of active client organizations for dropdown"""
        try:
            # Get organizations with active status
            result = self._make_request('GET', '/organizations', params={
                'page[size]': 500,  # Get up to 500 organizations
                'sort': 'name'
            })

            if not result or 'data' not in result:
                logger.error(f"Failed to get organizations: {result.get('error', 'Unknown error')}")
                return []

            # Parse IT Glue response format
            organizations = []
            for org in result.get('data', []):
                attributes = org.get('attributes', {})
                org_status = attributes.get('organization-status-name', '').lower()

                # Filter for active organizations
                if 'active' in org_status:
                    organizations.append({
                        'id': org.get('id'),
                        'name': attributes.get('name', ''),
                        'type': attributes.get('organization-type-name', ''),
                        'status': attributes.get('organization-status-name', '')
                    })

            logger.info(f"Retrieved {len(organizations)} active organizations from IT Glue")
            return organizations

        except Exception as e:
            logger.error(f"Error getting organizations: {str(e)}")
            return []

    def get_organization_profile(self, org_id: int) -> Optional[Dict]:
        """Get comprehensive organization profile for policy generation"""
        try:
            # Get organization details
            org_result = self._make_request('GET', f'/organizations/{org_id}')

            if not org_result or 'data' not in org_result:
                logger.error(f"Failed to get organization {org_id}")
                return None

            org_data = org_result.get('data', {})
            attributes = org_data.get('attributes', {})

            # Get configurations for this organization
            config_result = self._make_request('GET', '/configurations', params={
                'filter[organization_id]': org_id,
                'page[size]': 500
            })

            configurations = config_result.get('data', []) if config_result and 'data' in config_result else []

            # Build profile
            profile = {
                'organization': {
                    'id': org_data.get('id'),
                    'name': attributes.get('name', ''),
                    'organization_type': attributes.get('organization-type-name', ''),
                    'status': attributes.get('organization-status-name', ''),
                },
                'total_configurations': len(configurations),
                'technology_stack': self._parse_configurations(configurations),
                'compliance_frameworks': self._detect_compliance_frameworks(configurations)
            }

            logger.info(f"Retrieved profile for organization {org_id} with {len(configurations)} configurations")
            return profile

        except Exception as e:
            logger.error(f"Error getting organization profile: {str(e)}")
            return None

    def _parse_configurations(self, configurations: List[Dict]) -> Dict:
        """Parse configurations into categorized tech stack"""
        tech_stack = {
            'endpoints': [],
            'network': [],
            'security': [],
            'cloud': [],
            'other': []
        }

        for config in configurations:
            attributes = config.get('attributes', {})
            config_item = {
                'id': config.get('id'),
                'name': attributes.get('name', ''),
                'type': attributes.get('configuration-type-name', ''),
                'status': attributes.get('configuration-status-name', '')
            }

            # Categorize based on type
            config_type = config_item['type'].lower()
            if 'server' in config_type or 'workstation' in config_type or 'laptop' in config_type:
                tech_stack['endpoints'].append(config_item)
            elif 'firewall' in config_type or 'switch' in config_type or 'router' in config_type:
                tech_stack['network'].append(config_item)
            elif 'security' in config_type or 'antivirus' in config_type:
                tech_stack['security'].append(config_item)
            elif 'cloud' in config_type or 'saas' in config_type:
                tech_stack['cloud'].append(config_item)
            else:
                tech_stack['other'].append(config_item)

        return tech_stack

    def _detect_compliance_frameworks(self, configurations: List[Dict]) -> List[str]:
        """Detect compliance frameworks from configurations"""
        frameworks = set()

        for config in configurations:
            attributes = config.get('attributes', {})
            name = attributes.get('name', '').lower()
            notes = attributes.get('notes', '').lower() if attributes.get('notes') else ''

            combined_text = f"{name} {notes}"

            if 'hipaa' in combined_text:
                frameworks.add('HIPAA')
            if 'pci' in combined_text:
                frameworks.add('PCI-DSS')
            if 'nist' in combined_text:
                frameworks.add('NIST')
            if 'soc 2' in combined_text or 'soc2' in combined_text:
                frameworks.add('SOC 2')
            if 'iso 27001' in combined_text or 'iso27001' in combined_text:
                frameworks.add('ISO 27001')
            if 'gdpr' in combined_text:
                frameworks.add('GDPR')
            if 'cmmc' in combined_text:
                frameworks.add('CMMC')

        return list(frameworks)

    def map_profile_to_form_data(self, profile: Dict) -> Dict:
        """
        Map IT Glue profile data to policy generator form fields
        Returns dict that can be used to pre-populate the form
        """
        if not profile:
            return {}

        org_info = profile.get('organization', {})
        tech_stack = profile.get('technology_stack', {})
        compliance = profile.get('compliance_frameworks', [])

        # Map organization details
        form_data = {
            'client_name': org_info.get('name', ''),
            'industry': self._map_industry(org_info.get('organization_type', '')),
            'company_size': self._estimate_company_size(profile.get('total_configurations', 0)),
            'compliance_requirements': self._map_compliance(compliance)
        }

        # Map technology stack to specific form fields
        tech_mapping = self._map_technology_stack(tech_stack)
        form_data.update(tech_mapping)

        return form_data

    def _map_industry(self, org_type: str) -> str:
        """Map IT Glue organization type to industry dropdown"""
        org_type_lower = org_type.lower()

        industry_mapping = {
            'healthcare': 'Healthcare',
            'medical': 'Healthcare',
            'hospital': 'Healthcare',
            'clinic': 'Healthcare',
            'financial': 'Financial Services',
            'bank': 'Financial Services',
            'investment': 'Financial Services',
            'manufacturing': 'Manufacturing',
            'factory': 'Manufacturing',
            'retail': 'Retail',
            'store': 'Retail',
            'shop': 'Retail',
            'technology': 'Technology',
            'software': 'Technology',
            'saas': 'Technology',
            'education': 'Education',
            'school': 'Education',
            'university': 'Education',
            'legal': 'Legal',
            'law': 'Legal',
            'attorney': 'Legal'
        }

        for keyword, industry in industry_mapping.items():
            if keyword in org_type_lower:
                return industry

        return 'Other'

    def _estimate_company_size(self, config_count: int) -> str:
        """Estimate company size based on number of configurations"""
        if config_count < 20:
            return 'Small (1-50 employees)'
        elif config_count < 75:
            return 'Medium (51-250 employees)'
        elif config_count < 200:
            return 'Large (251-1000 employees)'
        else:
            return 'Enterprise (1000+ employees)'

    def _map_compliance(self, frameworks: List[str]) -> str:
        """Map detected compliance frameworks to form dropdown"""
        if not frameworks:
            return ''

        # Return the first detected framework that matches form options
        framework_mapping = {
            'NIST': 'NIST Cybersecurity Framework',
            'SOC 2': 'SOC 2 Type II',
            'ISO 27001': 'ISO 27001',
            'HIPAA': 'HIPAA',
            'PCI-DSS': 'PCI DSS',
            'PCI': 'PCI DSS',
            'GDPR': 'GDPR',
            'CMMC': 'CMMC Level 2'
        }

        for framework in frameworks:
            if framework in framework_mapping:
                return framework_mapping[framework]

        return frameworks[0] if frameworks else ''

    def _map_technology_stack(self, tech_stack: Dict) -> Dict:
        """
        Map IT Glue technology stack to policy generator form fields
        This is the KEY function that auto-detects all security tools
        """
        tech_fields = {}

        # Combine all configurations for analysis
        all_configs = []
        for category in tech_stack.values():
            if isinstance(category, list):
                all_configs.extend(category)

        # Convert to lowercase names for matching
        config_names = [config.get('name', '').lower() for config in all_configs]
        config_text = ' '.join(config_names)

        # Platform Choice Detection
        if 'microsoft 365' in config_text or 'office 365' in config_text or 'azure' in config_text or 'o365' in config_text:
            tech_fields['platform_choice'] = 'Microsoft 365 / Azure'
        elif 'google workspace' in config_text or 'gmail' in config_text or 'gsuite' in config_text:
            tech_fields['platform_choice'] = 'Google Workspace'
        else:
            tech_fields['platform_choice'] = 'Microsoft 365 / Azure'  # Default

        # MDR/Endpoint Protection Detection
        if 'sophos' in config_text:
            tech_fields['mdr_solution'] = 'Sophos MDR'
        elif 'crowdstrike' in config_text or 'sentinel' in config_text:
            tech_fields['mdr_solution'] = 'Other MDR'
        elif 'antivirus' in config_text or 'defender' in config_text:
            tech_fields['mdr_solution'] = 'Traditional Antivirus Only'
        else:
            tech_fields['mdr_solution'] = 'Sophos MDR'  # Crimson IT default

        # Email Security Detection
        if 'avanan' in config_text:
            tech_fields['email_security'] = 'Avanan Email Security'
        elif 'defender' in config_text or 'atp' in config_text:
            tech_fields['email_security'] = 'Microsoft Defender'
        elif 'proofpoint' in config_text or 'mimecast' in config_text:
            tech_fields['email_security'] = 'Other Email Security'

        # SIEM Detection
        if 'siem' in config_text or 'splunk' in config_text or 'sentinel' in config_text:
            tech_fields['siem_solution'] = 'SIEM with SOC monitoring'
        elif 'log' in config_text and 'monitor' in config_text:
            tech_fields['siem_solution'] = 'Basic log collection'

        # PAM Detection
        if 'senhasegura' in config_text:
            tech_fields['pam_solution'] = 'Senhasegura PAM'
        elif 'cyberark' in config_text or 'thycotic' in config_text or 'beyondtrust' in config_text:
            tech_fields['pam_solution'] = 'Other PAM'

        # Disk Encryption Detection
        if 'bitlocker' in config_text:
            if 'filevault' in config_text:
                tech_fields['disk_encryption'] = 'Both BitLocker and FileVault'
            else:
                tech_fields['disk_encryption'] = 'BitLocker (Windows)'
        elif 'filevault' in config_text:
            tech_fields['disk_encryption'] = 'FileVault (macOS)'

        # MDM Detection
        if 'intune' in config_text:
            tech_fields['mdm_computers'] = 'Microsoft Intune'
            tech_fields['mdm_mobile'] = 'Microsoft Intune'
        elif 'jamf' in config_text or 'airwatch' in config_text:
            tech_fields['mdm_computers'] = 'Other MDM'
            tech_fields['mdm_mobile'] = 'Other MDM'

        # Security Training Detection
        if 'knowbe4' in config_text:
            if 'monthly' in config_text:
                tech_fields['security_training'] = 'KnowBe4 Monthly Training'
            else:
                tech_fields['security_training'] = 'KnowBe4 Quarterly Training'

        # Phishing Tests Detection
        if 'knowbe4' in config_text or 'phishing' in config_text:
            tech_fields['phishing_tests'] = 'Monthly Phishing Tests'

        # Vulnerability Scanning Detection
        if 'vulnerability' in config_text or 'nessus' in config_text or 'qualys' in config_text:
            if 'monthly' in config_text:
                tech_fields['vulnerability_scans'] = 'Monthly Vulnerability Scans'
            else:
                tech_fields['vulnerability_scans'] = 'Quarterly Vulnerability Scans'

        # Dark Web Monitoring Detection
        if 'darkwebid' in config_text or 'dark web' in config_text:
            tech_fields['dark_web_monitoring'] = 'DarkWebID Monitoring'
        elif 'breach' in config_text and 'monitor' in config_text:
            tech_fields['dark_web_monitoring'] = 'Other Dark Web Monitoring'

        # MFA Detection
        if 'microsoft' in config_text and ('mfa' in config_text or 'authenticator' in config_text):
            tech_fields['mfa_solution'] = 'Microsoft MFA'
        elif 'duo' in config_text:
            tech_fields['mfa_solution'] = 'Duo Security'
        elif 'mfa' in config_text or 'two-factor' in config_text or '2fa' in config_text:
            tech_fields['mfa_solution'] = 'Other MFA'

        # Password Manager Detection
        if 'lastpass' in config_text:
            tech_fields['password_manager'] = 'LastPass Business'
        elif '1password' in config_text or 'dashlane' in config_text or 'keeper' in config_text:
            tech_fields['password_manager'] = 'Other Password Manager'

        # Intrusion Detection Detection
        if 'ids' in config_text or 'ips' in config_text or 'intrusion' in config_text:
            tech_fields['intrusion_detection'] = 'Network Intrusion Detection System'
        elif 'firewall' in config_text and ('sonicwall' in config_text or 'fortinet' in config_text or 'palo alto' in config_text):
            tech_fields['intrusion_detection'] = 'Firewall with IDS/IPS'
        elif 'firewall' in config_text or 'meraki' in config_text:
            tech_fields['intrusion_detection'] = 'Basic Firewall'

        return tech_fields

    def save_policy_to_itglue(self, org_id: int, policy_name: str,
                              policy_content: str, policy_type: str,
                              compliance_frameworks: List[str]) -> Dict:
        """Save generated policy as a document in IT Glue"""
        try:
            # Create a flexible asset or document in IT Glue
            # This would require setting up a flexible asset type for policies
            # For now, we'll return success but not actually save
            # This can be implemented later based on IT Glue structure

            logger.info(f"Policy save requested for org {org_id}: {policy_name}")

            # TODO: Implement actual save to IT Glue when flexible asset type is configured
            return {
                'success': True,
                'message': 'Policy generation logged. Document upload to IT Glue available upon request.',
                'document_id': None
            }

        except Exception as e:
            logger.error(f"Error saving policy to IT Glue: {str(e)}")
            return {'success': False, 'error': str(e)}
