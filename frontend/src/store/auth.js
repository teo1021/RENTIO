let token = localStorage.getItem('rentio_token');
let user = null;

export function getToken() {
  return token;
}

export function getUser() {
  return user;
}

export function setSession(nextUser, nextToken) {
  token = nextToken;
  user = nextUser;
  localStorage.setItem('rentio_token', nextToken);
  window.dispatchEvent(new CustomEvent('rentio:auth-change'));
}

export function setUser(nextUser) {
  user = nextUser;
  window.dispatchEvent(new CustomEvent('rentio:auth-change'));
}

export function logout() {
  token = null;
  user = null;
  localStorage.removeItem('rentio_token');
  window.dispatchEvent(new CustomEvent('rentio:auth-change'));
}

export function hasSession() {
  return Boolean(token && user);
}
