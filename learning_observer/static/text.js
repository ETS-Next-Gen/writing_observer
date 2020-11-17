export const name = 'student_text';

export function student_text(div, text) {
    var start = 0;
    var stop = 1;
    const MAXIMUM_LENGTH = 250;

    div.text(text);
/*
	.substr(start, stop-start));
	stop = stop + 1;
	
	if(stop > text.length) {
	    stop = 1;
	    start = 0;
	}
    
	start = Math.max(start, stop-MAXIMUM_LENGTH);
	while((text[start] != ' ') && (start>0) && (start<text.length) ) {
	    start++;
	}
	if(start>stop) {
	    start=stop;
	}

	if(div.size() > 0) {
	    setTimeout(updateText, sample_ici(ici));
	};
    }
    setTimeout(updateText, sample_ici(50));*/
}

//typing();

d3.select(".textdebug-text").call(student_text);

