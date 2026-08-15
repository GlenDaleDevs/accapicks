// Central route builders — keeps path strings in one place so a future
// restructure doesn't mean grepping for template literals again.

export const groupAcca = (groupId) => `/g/${groupId}/acca`;
export const groupFixtures = (groupId) => `/g/${groupId}/fixtures`;
export const groupTable = (groupId) => `/g/${groupId}/table`;
export const groupMore = (groupId) => `/g/${groupId}/more`;
export const memberPicks = (groupId, userId) => `/g/${groupId}/more/members/${userId}`;
export const accaDetail = (groupId, accaId) => `/g/${groupId}/accas/${accaId}`;

export const SETTINGS = "/settings";

// Last group the user viewed. Cleared on logout — see handleLogout in App.jsx.
export const LAST_GROUP_KEY = "lastGroupId";

export function readLastGroupId() {
  return localStorage.getItem(LAST_GROUP_KEY);
}

export function writeLastGroupId(groupId) {
  localStorage.setItem(LAST_GROUP_KEY, String(groupId));
}

export function clearLastGroupId() {
  localStorage.removeItem(LAST_GROUP_KEY);
}
