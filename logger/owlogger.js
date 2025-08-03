class Stat {
    constructor( name ) {
        this.lines = 0;
        this.name = name ;
        //  Calculation from Wikipedia article
        this.n = 0;
        this.Q = 0.;
        this.A = 0.;
        this.max = null ;
        this.min = null ;
    }
    add( lines ) {
        this.lines += 1;
        lines.forEach( x => {
            this.n += 1 ;
            this.Q += (this.n-1)*(x-this.A)**2/this.n
            this.A += (x-this.A)/this.n ;
            if ( this.n == 1 ) {
                this.max = x ;
                this.min = x ;
            } else {
                this.max = Math.max( x, this.max ) ;
                this.min = Math.min( x, this.min ) ;
            }
        });
    }
    Max() {
        return this.max ;
    }
    Min() {
        return this.min ;
    }
    Lines() {
        return this.lines ;
    }
    N() {
        return this.n;
    }
    Avg() {
        return this.A ;
    }
    Std() {
        return Math.sqrt( this.Q/this.n ) ;
    }
    Name() {
        return this.name ;
    }
}
class StatList {
    constructor( data ) {
        this.all = new Stat("All") ;
        this.list = {} ;
        data.forEach( dline => this.addline(dline) );
    }
    addline( dline ) {
        const numbers = ((dline[2].match(/-?(\d+\.?\d*|\.?\d+)/g))??[]).map(Number) ;
        this.all.add(numbers);
        const key = dline[1] ;
        if ( !(key in this.list) ) {
            this.list[key] = new Stat(key) ;
        }
        this.list[key].add(numbers);
    }
    All() {
        return this.all ;
    }
    Keys() {
        return Object.keys(this.list) ;
    }
    Stat(key) {
        return this.list[key] ;
    }
}
class Swipe {
    constructor() {
        this.thresholdX = 100;
        this.thresholdY = 31;
        window.addEventListener('touchstart', (event)=>this.start(event) ); 
        window.addEventListener('touchend',   (event)=>this.stop(event)  ); 
    }
    start( event ) {
        this.initialX = event.touches[0].clientX;
        this.initialY = event.touches[0].clientY;
    }
    stop() {
        const deltaX = this.initialX - event.changedTouches[0].clientX;
        const deltaY = this.initialY - event.changedTouches[0].clientY;
        if ( Math.abs(deltaY) < this.thresholdY ) {
            if ( deltaX > this.thresholdX ) {
                let copy = new Date(globals.daystart.valueOf());
                NewDate( new Date(copy.setDate(copy.getDate()-1)) );
            } else if ( deltaX < -this.thresholdX ) {
                let copy = new Date(globals.daystart.valueOf());
                NewDate( new Date(copy.setDate(copy.getDate()+1)) );
            }
        }
    }
}
function YYYYMMDD(date) {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
}
function NewDate(date) {
    const url = new URL(location.href);
    url.searchParams.set('date', YYYYMMDD(date));
    url.searchParams.set('type', globals.page_type);
    location.assign(url.search);
}
function NewType(ntype) {
    const url = new URL(location.href);
    url.searchParams.set('date', YYYYMMDD(globals.daystart));
    url.searchParams.set('type', ntype);
    location.assign(url.search);
}
function CreateDataTable() {
    const table = document.getElementById("table");
    table.innerHTML="";
    const sym=(i,s0,s1)=>{
        if (i!=s0){return "&nbsp";}
        if ( s1>0){return "&uarr;";}
        return "&darr;";
    }
    sortorder = JSON.parse(sessionStorage.getItem("sortorder"));
    const head = table.createTHead().insertRow(-1);
    ["Time","Source","Data"].forEach( (h,i) => head.insertCell(-1).innerHTML=`<span onclick="SortOn(${i})"><B>${h}&nbsp;${sym(i,sortorder[0],sortorder[1])}</B></span>` );
    const body = table.createTBody();
    globals.dayData.forEach( r => AddRow( body, r ) );
}
function CreateStatTable() {
    const table = document.getElementById("table");
    table.innerHTML="";
    const head = table.createTHead().insertRow(-1);
    ["Source","Types","Values"].forEach( (h,i) => head.insertCell(-1).innerHTML=`<B>${h}</B>` );
    const statData = new StatList( globals.dayData ) ;
    const body = table.createTBody();
    statData.Keys().map( k=> statData.Stat(k)).forEach( s => AddStat( table, s ) ) ;
    AddStat( table, statData.All() );
}                  
function AddRow( table, row_data ) {
    const row = table.insertRow(-1);
    row_data.forEach( d => row.insertCell(-1).innerHTML=d );
}
function AddStat( table, stat ) {
    AddRow( table, [`<B>${stat.Name()}</B>`, "Lines, Readings", `${stat.Lines()}, ${stat.N()}`]);
    AddRow( table, ["", "Avg (Std)", (stat.N()==0)?"":`${stat.Avg().toFixed(2)} (${stat.Std().toFixed(2)})`]);
    AddRow( table, ["", "Range", (stat.N()==0)?"":`${stat.Min()} &mdash; ${stat.Max()}`]);
}          
function SortOn( column=null ){
    const so = sessionStorage.getItem("sortorder");
    let sortorder = [0,1] ;
    if ( so != null ) {
        sortorder = JSON.parse(so);
    }
    if ( column != null ) {
        if ( column==sortorder[0] ) {
            sortorder[1] = -sortorder[1] ;
        } else {
            sortorder = [column, 1];
        }
    }
    if ( sortorder[1] > 0 ) {
        globals.dayData.sort( (r1,r2) => r1[sortorder[0]].localeCompare(r2[sortorder[0]]) );
    } else {
        globals.dayData.sort( (r2,r1) => r1[sortorder[0]].localeCompare(r2[sortorder[0]]) );
    }
    sessionStorage.setItem("sortorder",JSON.stringify(sortorder));
    CreateDataTable();
}
function TestDate(x) {
    switch (x.cellType) {
        case 'day':
            return globals.goodDays.includes(YYYYMMDD(x.date));
        case 'month':
            return globals.goodMonths.includes(YYYYMMDD(x.date));
        case 'year':
            return globals.goodYears.includes(YYYYMMDD(x.date));
        default:
            return false;
    }
}
window.onload = () => {

    globalThis.dp = new AirDatepicker("#new_cal", {
            onSelect(x) {NewDate(x.date)},
            isMobile:true,
            buttons:[{content:'Today',onClick:(dp)=>NewDate(new Date())}],
            selectedDates:[globals.daystart],
            onRenderCell(x) { if (TestDate(x)) { return {classes:'present'};} },
    } ) ;
    var swipe = new Swipe() ;
    document.getElementById("date").innerHTML = globals.header_date;
    document.getElementById("time").innerHTML = globals.header_time;
    document.getElementById("showdate").innerHTML = globals.daystart.toLocaleDateString();
    switch (globals.page_type) {
        case "stat":
            document.getElementById("stat").classList.add("disabled-link");
            document.getElementById("table").classList.add("statTable");
            CreateStatTable() ;
            break ;
        case "plot":
            document.getElementById("plot").classList.add("disabled-link");
            break ;
        default: // "data"
            document.getElementById("data").classList.add("disabled-link");
            document.getElementById("table").classList.add("dataTable");
            SortOn() ;
            break ;
    }
    
}

