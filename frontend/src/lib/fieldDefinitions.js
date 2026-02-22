/** Static metadata for onboarding steps and fields. */

export const STEPS = [
  {
    key: 'profile',
    label: 'Profile',
    fields: [
      { key: 'display_name', label: 'Display Name', type: 'text' },
      {
        key: 'age_range', label: 'Age Range', type: 'enum',
        options: [
          { value: 'under_18', label: 'Under 18' },
          { value: '18_24', label: '18-24' },
          { value: '25_34', label: '25-34' },
          { value: '35_44', label: '35-44' },
          { value: '45_plus', label: '45+' },
        ],
      },
      { key: 'country', label: 'Country', type: 'text' },
    ],
  },
  {
    key: 'food',
    label: 'Food',
    fields: [
      {
        key: 'diet', label: 'Diet', type: 'enum',
        options: [
          { value: 'omnivore', label: 'Omnivore' },
          { value: 'vegetarian', label: 'Vegetarian' },
          { value: 'vegan', label: 'Vegan' },
          { value: 'pescatarian', label: 'Pescatarian' },
          { value: 'keto', label: 'Keto' },
          { value: 'halal', label: 'Halal' },
          { value: 'kosher', label: 'Kosher' },
          { value: 'other', label: 'Other' },
        ],
      },
      {
        key: 'allergies', label: 'Allergies', type: 'multi',
        options: [
          { value: 'dairy', label: 'Dairy' },
          { value: 'gluten', label: 'Gluten' },
          { value: 'nuts', label: 'Nuts' },
          { value: 'shellfish', label: 'Shellfish' },
          { value: 'soy', label: 'Soy' },
          { value: 'eggs', label: 'Eggs' },
          { value: 'none', label: 'None' },
        ],
      },
      {
        key: 'spice_ok', label: 'Spice OK?', type: 'enum',
        options: [
          { value: true, label: 'Yes' },
          { value: false, label: 'No' },
        ],
      },
    ],
  },
  {
    key: 'anime',
    label: 'Anime',
    fields: [
      {
        key: 'favorite_genres', label: 'Favorite Genres', type: 'multi',
        options: [
          { value: 'shonen', label: 'Shonen' },
          { value: 'shojo', label: 'Shojo' },
          { value: 'seinen', label: 'Seinen' },
          { value: 'isekai', label: 'Isekai' },
          { value: 'mecha', label: 'Mecha' },
          { value: 'slice_of_life', label: 'Slice of Life' },
          { value: 'horror', label: 'Horror' },
          { value: 'romance', label: 'Romance' },
          { value: 'comedy', label: 'Comedy' },
          { value: 'fantasy', label: 'Fantasy' },
          { value: 'sci_fi', label: 'Sci-Fi' },
        ],
      },
      {
        key: 'sub_or_dub', label: 'Sub or Dub', type: 'enum',
        options: [
          { value: 'sub', label: 'Sub' },
          { value: 'dub', label: 'Dub' },
          { value: 'both', label: 'Both' },
        ],
      },
      { key: 'top_3_anime', label: 'Top 3 Anime', type: 'list' },
    ],
  },
]

/** Build a {value → label} map from a field's options array. */
function optionMap(fieldDef) {
  if (!fieldDef.options) return null
  const m = {}
  for (const o of fieldDef.options) m[String(o.value)] = o.label
  return m
}

/** Format a field value for display in the side panel. */
export function formatFieldValue(fieldDef, value) {
  if (value == null) return ''

  if (fieldDef.type === 'multi' && Array.isArray(value)) {
    const map = optionMap(fieldDef)
    return value.map(v => map?.[v] ?? v).join(', ')
  }

  if (fieldDef.type === 'enum') {
    const map = optionMap(fieldDef)
    return map?.[String(value)] ?? String(value)
  }

  if (fieldDef.type === 'list' && Array.isArray(value)) {
    return value.join(', ')
  }

  return String(value)
}
