.PHONY: dist clean buildWorkflow release

distDir=./dist
workflowName="displayplacer.alfredworkflow"

dist: | buildWorkflow
clean:
	rm -rf $(distDir)/*

buildWorkflow:
	$(shell [ ! -d "$(distDir)" ] && mkdir -p "$(distDir)")
	cp -fv $(PWD)/icon.png $(distDir)
	cp -fv $(PWD)/*.py $(distDir)
	cp -fv $(PWD)/LICENSE $(distDir)
	cp -fv $(PWD)/info.plist $(distDir)
	cd $(distDir) && zip -r $(workflowName) * -x "*.DS_Store"

release: | dist
	cp -fv $(distDir)/$(workflowName) .
