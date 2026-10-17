// The matchmaker keys off orientation, so map "who you like" back to the values it expects:
// male->women or female->men -> straight, male->men -> gay, female->women -> lesbian, everyone -> bisexual.
export function deriveOrientation(gender: string, interestedIn: string) {
	if (interestedIn === 'everyone') return 'bisexual';
	const likesSameGender = (gender === 'male') === (interestedIn === 'men');
	if (!likesSameGender) return 'straight';
	return gender === 'male' ? 'gay' : 'lesbian';
}
