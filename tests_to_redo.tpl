
<h1> Tests to redo (DBPhone) - Week {{week}}</h1>

<script>
    $('#more').click(function () {
if($('button span').hasClass('glyphicon-chevron-down'))
{
    $('#more').html('<span class="glyphicon glyphicon-chevron-up"></span> Less Info');
}
else
{
    $('#more').html('<span class="glyphicon glyphicon-chevron-down"></span> More Info');
}
});
</script>


<div class="container">



    <table class="table table-hover table-striped">
        <thead>
        <tr>
            <th class="text-left">Category</th>
            <th class="text-left">Number of tests to clean</th>
            <th class="text-left">Tunedfields</th>
            <th class="text-left">Evolution (3 weeks)</th>
        </tr>
        </thead>
%from collections import Counter
%for key, value in sorted(stats_categories[week].iteritems(), key=lambda x:x[1], reverse=True):
    <tr>
        <td class="text-left">{{key[0]}}</td>
        <td class="text-left">{{value[0]}}</td>
        <td class="text-left">
            <script>
$(document).ready(function() {
    $('#toggle_{{key[0]}}').click(function() {
    $('#tunedfields_{{key[0]}}').toggle('fast');
    });
    })
    </script>
            <script>

    $('#t_{{key[0]}}').on('shown.bs.collapse', function () {
       $(".glyphicon").removeClass("glyphicon-chevron-up").addClass("glyphicon-chevron-down");
    });

    $('#t_{{key[0]}}').on('hidden.bs.collapse', function () {
       $(".glyphicon").removeClass("glyphicon-chevron-down").addClass("glyphicon-chevron-up");
    });
            </script>

                <button data-toggle="collapse" data-target="#t_{{key[0]}}"><i class="glyphicon glyphicon-large glyphicon-chevron-up"></i></button>
            <div class="collapse" id="t_{{key[0]}}">
            <table class="table table-hover table-striped" id="tunedfields_{{key[0]}}">
                        <thead>
                        <tr>
                            <th class="text-left">Name</th>
                            <th class="text-left">Number of tests to clean</th>
                            <th class="text-left">Evolution (3 weeks)</th>
                        </tr>
                        </thead>
            %for key_t, val_t in sorted(Counter([v for y in value[1] for v in y]).iteritems(), key=lambda x: x[1], reverse=True):
                % evol_tunedfield = val_t - Counter([val for y in stats_categories[week - 3][key][1] for val in y])[key_t]
                % if evol_tunedfield > 0:
                    <tr style="color:red; font-weight:bold"><td class="text-left" >{{key_t}}</td><td>{{val_t}}</td><td>{{evol_tunedfield}}</td></tr>
                %elif evol_tunedfield < 0:
                    <tr style="color:green; font-weight:bold"><td class="text-left">{{key_t}}</td><td>{{val_t}}</td><td>{{evol_tunedfield}}</td></tr>
                %else:
                    <tr><td class="text-left">{{key_t}}</td><td>{{val_t}}</td><td>{{evol_tunedfield}}</td></tr>
                %end
            %end
            </table>
            </div>
        </td>
        <td class="text-center">
            {{sum([v for _, v in Counter([v for y in value[1] for v in y]).iteritems()]) - sum([v for _, v in Counter([v for y in stats_categories[week - 3][key][1] for v in y]).iteritems()])}}
            <a href="static/img/{{key[0]}}.svg" target="popup" onclick='window.open(this.href,"popupwindow", "width=1000,height=600,scrollbars,toolbar=0,resizable"); return false;' Target='_blank'><img src="static/img/graph.png"/></a>
        </td>

    </tr>
%end
    </table>
</div>

