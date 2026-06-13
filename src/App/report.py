class ReportGenerator:
    @staticmethod
    def generate_report(url, prediction_result):
        """Generate a formatted report for the prediction"""
        prediction = prediction_result['prediction']
        prob_phish = prediction_result['probability_phishing']
        prob_legit = prediction_result['probability_legitimate']

        result = "Phishing" if prediction == 1 else "Legitimate"

        report = {
            'url': url,
            'result': result,
            'confidence': max(prob_phish, prob_legit),
            'probability_phishing': prob_phish,
            'probability_legitimate': prob_legit,
            'status': 'success'
        }

        return report

    @staticmethod
    def generate_error_report(url, error_message):
        """Generate error report"""
        return {
            'url': url,
            'result': 'Error',
            'error': error_message,
            'status': 'error'
        }