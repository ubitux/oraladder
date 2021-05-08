function replay_render(data, type, row, meta) {
	if (data == undefined)
		return ''
	var replay = '<a href="' + data.url + '" title="Download">📥</a>'
	if (!data.supports_analysis)
		return replay
	var info_url = 'https://dragunoff.github.io/OpenRA-replay-analytics/#/oraladder/' + data.hash
	var info = '<a href="' + info_url + '" title="Information/Analysis">🔍</a>'
	return replay + ' ' + info
}

function get_diff_html(diff) {
	var cls = 'diff' + (diff >= 0 ? 'up' : 'down');
	return '<span class=' + cls + '>' + diff + '</span>'
}

function get_player_html(name, url, avatar_url) {
	var avatar_img = avatar_url ? '<img src="' + avatar_url + '" alt="">' : ''
	var avatar = '<div class=avatar>' + avatar_img + '</div>'
	return avatar + '<a href="' + url + '">' + name + '</a>'
}

function player_with_diff_render(data, type, row, meta) {
	if (data == undefined)
		return '<span class=ghost>ghost</span>'
	var player = '<a href="' + data.url + '">' + data.name + '</a>'
	return player + ' ' + get_diff_html(data.diff)
}

function player_render(data, type, row, meta) {
	if (data == undefined)
		return '<span class=ghost>ghost</span>'
	return get_player_html(data.name, data.url, data.avatar_url)
}

function rating_render(data, type, row, meta) {
	return data.value + ' ' + get_diff_html(data.diff)
}

function winrate_render(data, type, row, meta) {
	return data.toFixed(1) + '%'
}

function outcome_render(data, type, row, meta) {
	return data.desc + ' ' + get_diff_html(data.diff)
}
