#!/usr/bin/env ruby

level = 0
toc_output = ""

pre_toc = ""
post_toc = ""

pos = :pre_toc

File.new("manual.html").each_line { |line|
  case pos
  when :pre_toc
    if line.include? '<div class="toc">'
      pos = :toc
    else
      pre_toc << line
    end
  when :toc
    if line.include? '</div>'
      pos = :post_toc
    end
  when :post_toc
    md = /<h(\d) id=\"([^"]+)\">(.*)<\/h/.match(line)
    if md
      l = md[1].to_i
      i = md[2]
      t = md[3]

      if level < l
        while level < l
          toc_output << "<ol>\n" 
          level +=1 
        end
      else
        while level > l
          toc_output << "</li>\n</ol>\n" 
          level -=1 
        end
        (toc_output.length > 0) and (toc_output << "</li>\n")
      end
      toc_output << "<li><a href=\"\##{i}\">#{t}</a>"
    end
    post_toc << line
  end
}

while level != 0
  level -= 1
  toc_output << "</li></ol>\n"
end

f2 = File.open("manual.html", "w")

f2.puts pre_toc
f2.puts "<div class=\"toc\">\n" + toc_output + "\n</div>"
f2.puts post_toc
f2.close
