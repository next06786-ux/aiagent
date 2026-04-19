import { useMemo } from 'react';
import { validatePassword, type PasswordStrength } from '../../utils/passwordValidator';
import './PasswordStrengthIndicator.css';

interface PasswordStrengthIndicatorProps {
  password: string;
  show?: boolean;
}

export function PasswordStrengthIndicator({
  password,
  show = true,
}: PasswordStrengthIndicatorProps) {
  const strength: PasswordStrength = useMemo(
    () => validatePassword(password),
    [password]
  );

  if (!show || !password) {
    return null;
  }

  const getColorClass = () => {
    switch (strength.level) {
      case 'weak':
        return 'strength-weak';
      case 'medium':
        return 'strength-medium';
      case 'strong':
        return 'strength-strong';
      case 'very-strong':
        return 'strength-very-strong';
      default:
        return '';
    }
  };

  return (
    <div className="password-strength-indicator">
      <div className="strength-bar-container">
        <div className={`strength-bar ${getColorClass()}`} style={{ width: `${(strength.score / 4) * 100}%` }} />
      </div>
      <div className="strength-info">
        <span className={`strength-label ${getColorClass()}`}>{strength.message}</span>
        {strength.suggestions.length > 0 && (
          <div className="strength-suggestions">
            <span className="suggestions-label">建议：</span>
            {strength.suggestions.join('、')}
          </div>
        )}
      </div>
    </div>
  );
}
