
// JQuery code to be added in here.
$('#likes').click(function() {
	var catid;
	catid = $(this).attr("data-catid");
	$.get('/rango/like_category/', {category_id: catid}, function(data) {
			$('#like_count').html(data);
			$('#likes').hide();
	});	
});

$('#suggestion').keyup(function(){
	var query;
	query = $(this).val();
	$.get('/rango/suggest_category/', {suggestion: query}, function(data){
	$('#cats').html(data);
	})
});

$('#auto_page').click(function() {
	var catid;
	var add_title;
	var add_url;
	catid = $(this).attr("data-catid");
	add_title = $(this).attr("data-title");
	add_url = $(this).attr("data-url");
	$.get('/rango/auto_add_page/', {category_id: catid, title: add_title, url: add_url}, function(data){
		$('#pages').html(data);
		$('#auto_page').hide();
	});	
});