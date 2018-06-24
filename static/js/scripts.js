$(document).ready(function(){
    $('p.sign-up').click(function(){
        $('.overlay').fadeToggle('slow');
    });

    $('.overlay').click(function(e){
        if (e.target == this) {
            $(this).fadeToggle();
         }
    });
});