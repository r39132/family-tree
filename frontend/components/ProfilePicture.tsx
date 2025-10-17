import { useState } from 'react';

type ProfilePictureProps = {
  firstName: string;
  lastName: string;
  profilePictureUrl?: string | null;
  size?: number;
  className?: string;
};

export default function ProfilePicture({
  firstName,
  lastName,
  profilePictureUrl,
  size = 50,
  className = '',
}: ProfilePictureProps) {
  const [imageError, setImageError] = useState(false);

  // Generate initials from first and last name
  const initials = `${firstName?.charAt(0) || ''}${lastName?.charAt(0) || ''}`.toUpperCase();

  // Generate a consistent color based on the name
  const getColorFromName = (name: string) => {
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    const hue = hash % 360;
    return `hsl(${hue}, 60%, 55%)`;
  };

  const backgroundColor = getColorFromName(`${firstName}${lastName}`);

  // Only show the profile picture if a valid URL exists
  // Don't show anything (no colored bubble/initials) if no profile picture
  const hasValidImage = profilePictureUrl && !imageError;

  // If no valid image, return null (don't render anything)
  if (!hasValidImage) {
    return null;
  }

  return (
    <div
      className={`profile-picture ${className}`}
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        overflow: 'hidden',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'transparent',
        flexShrink: 0,
      }}
    >
      <img
        src={profilePictureUrl}
        alt={`${firstName} ${lastName}`}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
        }}
        onError={() => setImageError(true)}
      />
    </div>
  );
}
