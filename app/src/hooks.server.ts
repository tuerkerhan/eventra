import { redirect, type Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
	// 1. Tarayıcıdaki çerezlerden (cookies) veya header'dan token'ı kontrol et
	const token = event.cookies.get('token'); 
	
	const isTargetingApp = event.url.pathname !== '/login';

	// 2. Eğer token yoksa ve kullanıcı login dışında bir sayfaya gitmeye çalışıyorsa
	if (!token && isTargetingApp) {
		// Doğrudan login sayfasına yönlendir
		throw redirect(303, '/login');
	}

	// 3. Eğer token VARSA ve kullanıcı hala /login sayfasına gitmeye çalışıyorsa dashboard'a at
	if (token && event.url.pathname === '/login') {
		throw redirect(303, '/');
	}

	// Her şey yolundaysa sayfayı normal şekilde yükle
	return resolve(event);
};